# dallas-res-watch

Read-only availability checker for Dallas restaurants and bars. For a **party of 4**, it lists the
open reservation times **5:00–10:00 PM Central** on every date **Nov 20–28, 2026**, then renders a
grid at `site/index.html`.

**It never books, holds, locks, or cancels anything.** Every request is the same anonymous
availability lookup the restaurant's own booking page makes. No accounts, no auth tokens.

## Run it locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # Playwright: only OpenTable/Tock need it
.venv/bin/python check.py                      # all platforms -> results.json
.venv/bin/python render.py                     # results.json -> site/index.html
open site/index.html

.venv/bin/python check.py --platforms resy,sevenrooms   # just some platforms
.venv/bin/python check.py --only monarch                # just matching venue names
.venv/bin/python diff.py old.json results.json          # newly opened slots since old.json
```

`check.py` flags:
- `--start-date 2026-11-20` / `--end-date 2026-11-28`
- `--party 4`
- `--window 17:00-22:00` (Central)
- `--delay 1.0-2.0` (seconds between requests)

Dates already in the past are marked `skipped`. When only some platforms run, rows for the others
are **kept** from the existing `results.json`. That lets the cloud runner and the Mac share one file.

`results.json` fields:
- top level: `generated_at`, `party`, `window`, `dates`, `venues[]`
- each venue: `name`, `platform`, `url`, `beli_avg`, `kind`
- `slots{date: ["5:30 PM", …]}` and `status{date: ok|none|error:…|skipped}`
- extras: `day_notes` (e.g. `closed`, `sold-out`) and `checked_at`

## How each platform works

| Platform | How | Where it runs | Requests per venue |
|---|---|---|---|
| Resy | `api.resy.com` JSON with Resy's public web api_key, no login: `/4/venue/calendar` once, then `/4/find` per open date | anywhere (cloud OK) | ≤ 10 |
| SevenRooms | widget API `/api-yoa/availability/ng/widget/range`, counts only `type == "book"` times | anywhere (cloud OK) | 3 (3-day chunks; `num_days` > 3 is rejected) |
| OpenTable | headless Chrome loads `/restaurant/profile/<rid>`, then runs the page's own `RestaurantsAvailability` GraphQL query in that tab with `forwardDays=8` (all 9 days per call) at 5 anchor times | **Mac only** (Akamai: 403 to GitHub runners, 403 to Playwright-launched headless, timeouts to curl) | 1 page + 5 queries |
| Tock | headless Chrome loads `exploretock.com/<slug>/search`; the page's own `calendar/full/v2` protobuf holds every date; we parse it (free = capacity − held − booked ≥ 4) | Mac (Cloudflare; untested from GitHub) | 1 page load |
| phone / walkin / unknown | not checked, shown as "call" / "walk-in" | — | 0 |

The browser is **always headless** (`--headless=new`). It never opens a window or takes focus, and
it uses its own profile at `~/.dallas-res-watch/chrome-profile` (override with `DRW_PROFILE`), never
your everyday Chrome profile. It launches the installed Google Chrome binary and attaches over CDP,
with the UA and client hints set to normal Chrome. That combination gets past OpenTable's Akamai
check (verified with a fresh, empty profile); Playwright's own headless launch gets 403.

Politeness: 1–2 s random delay between requests. Retries with backoff (2 s, 4 s, …) on 429, 5xx
and network errors. Each venue is wrapped in try/except, and so is the browser group, so one
failing venue or platform doesn't stop the run.

## Cloud + Mac schedule

- **GitHub Actions** (`.github/workflows/watch.yml`): every 3 h (and on demand) it runs
  `scripts/publish.sh resy,sevenrooms,phone,walkin,unknown`. That checks, renders, prints the diff
  to the job summary, and commits `results.json` + `site/`.
  - To run other platforms once, pass them in the workflow's `platforms` input. Playwright is
    installed only when OpenTable or Tock is requested.
  - Serve `site/` with GitHub Pages: Settings → Pages → deploy from a branch → `main` / root,
    then open `/site/`. Or move the output to `docs/` with `render.py --out docs/index.html`.
- **OpenTable + Tock on the Mac**: `bash scripts/publish.sh opentable,tock` checks those two,
  merges, renders, commits and pushes. To run it every 3 h with launchd:
  ```bash
  cp scripts/com.dallasreswatch.local.plist ~/Library/LaunchAgents/
  launchctl load ~/Library/LaunchAgents/com.dallasreswatch.local.plist    # unload to stop
  ```
  Logs go to `~/.dallas-res-watch/launchd.log`. The Mac must be awake.
- If the two sides push at the same time, `publish.sh` rebases and re-merges the other side's rows
  from `origin`, so neither overwrites the other. `NO_PUSH=1` only commits locally.
- Notifications: set `NTFY_TOPIC` (repo secret for the cloud; env var on the Mac) and
  `diff.py` posts newly opened slots to ntfy.sh. Off unless you set it.

## Adding venues

`venues.json` is a list of entries like this:

```json
{"name": "Monarch", "kind": "restaurant", "beli_avg": 8.9, "beli_ratings": 1200,
 "platform": "sevenrooms", "id": "monarchdallas",
 "url": "https://www.sevenrooms.com/reservations/monarchdallas", "phone": null, "notes": ""}
```

Easiest: `resolve.py` reads the booking URL and works out the platform and id. Add `--add` to write it:

```bash
.venv/bin/python resolve.py "<booking url>" --name "Monarch" --kind restaurant --beli 8.9 --ratings 1200 --add
```

By hand, per platform:

- **Resy** — `id` is an integer.
  - From `https://resy.com/cities/dallas-tx/venues/<slug>`:
    `curl -s -H 'Authorization: ResyAPI api_key="VbWk7s3L4KiK5fzlO7JD3Q5EYolJI7n5"' "https://api.resy.com/3/venue?url_slug=<slug>&location=dfw"`
    and read `id.resy`.
  - Or look in DevTools → Network for `venue_id=` on the `/4/find` request.
- **OpenTable** — `id` is the integer `rid`.
  - From `/restaurant/profile/<rid>`, or `?rid=` in a widget URL.
  - For an `/r/<slug>` URL, run `resolve.py`. It loads the page headlessly and reads
    `restaurantIds` from its availability query.
- **SevenRooms** — `id` is the venue slug.
  - It's the part after `/reservations/` (or `/explore/<slug>/`) in the widget URL.
  - Check it with
    `curl "https://www.sevenrooms.com/api-yoa/availability/ng/widget/range?venue=<slug>&party_size=4&start_date=2026-11-20&num_days=1&channel=SEVENROOMS_WIDGET"`.
    `status: 200` means it's right; 400 means a wrong slug.
- **Tock** — `id` is the first path segment of `https://www.exploretock.com/<slug>`.
  - Optional: `"tock_experiences": [ids]` pins specific experiences. Otherwise
    pickup/to-go/delivery experiences are dropped by name.
- **No online booking** — `"platform": "phone"` (put the number in `phone`), `"walkin"`, or
  `"unknown"`. These show as "call" / "walk-in" in the grid.

## Known quirks

- **Resy:** returns HTTP 500 to `/4/find` when the `Accept` header is sent *before*
  `Authorization`. `common.get_json` puts caller headers first.
- **Resy:** `/4/venue/calendar` reports `closed` / `sold-out` days. Those show `—` with a
  tooltip and skip the `/4/find` call.
- **OpenTable:**
  - Returns about 5 slots per day nearest each anchor time (17:30, 18:45, 20:00, 21:15, 22:00).
    A slot more than ~2 h from every anchor isn't possible inside the 5–10 PM window, but sparse
    days may show fewer times than exist.
  - The persisted-query hash in `platforms/opentable.py` can change when OpenTable ships. If
    every OpenTable venue errors with a GraphQL error, load any restaurant page with DevTools
    open, copy the new `sha256Hash` from the `RestaurantsAvailability` request, and update
    `PERSISTED_HASH`.
- **Tock:**
  - The protobuf layout is reverse-engineered. Free seats = field 4 − field 6 − field 7, with
    max party size (field 19) ≥ 4. Checked against the rendered "Book" buttons on 5 Dallas/Fort
    Worth venues on 2026-11-18.
  - There's no minimum-party field, so a large table that Tock wouldn't give to 4 could show as
    open.
