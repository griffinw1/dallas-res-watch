# Dallas project — master requirements

Two parts, one repo (`~/code/dallas-res-watch` → https://griffinw1.github.io/dallas-res-watch/).
Trip window: **Fri Nov 20 – Sat Nov 28, 2026** (Thanksgiving = Thu Nov 26).
Status key: ✅ done · 🔨 in progress · ⏳ blocked/waiting · ⬜ not started

## Global rules (both parts)
- **Read-only.** Never book, hold, cancel or join a waitlist anywhere. Every link opens the venue's own page.
- **Public pages.** First names only. No confirmation codes, emails, phone numbers of people, or addresses of private homes (e.g. the lakehouse).
- **Every outside link opens in a new tab** (`target="_blank" rel="noopener"`).
- Light + dark mode; works on a phone (16px side gutters, no sideways page scroll).
- Photos/menus are **linked or hot-linked from the venue's own listing or site** with a credit line; Beli member photos are never used.
- Git: commit only the files you own; push to `main`; on rejection `git pull --rebase` and retry.

---

## Part 1 — Reservation finder (`site/`)

### 1.1 Data: which venues
- ✅ 57 venues: Beli "Top 25 Restaurants in Dallas" + other highly rated restaurants + bars (`venues.json`).
- 🔨 **Real Beli community averages** (not the personal Rec Score), with rating count and top dishes, for every venue → `beli_avgs.jsonl`. Source: Beli iPhone app via iPhone Mirroring (`beli-lookup` skill). 5 of 57 done (Shoyo 9.3, Uchi 9.0, Mamani 9.0, Lucia 8.9, Bar Colette 8.5).
  ⏳ Needs ~1 hour with the Mac untouched (any mouse/keyboard use cancels it).
- ✅ Restaurants and bars kept as separate categories (`kind`).

### 1.2 Data: availability
- ✅ Party of 4, 5:00–10:00 PM Central, every date in the window.
- ✅ Platforms: Resy, OpenTable, SevenRooms, Tock (online); phone / walk-in / unknown labelled.
- ✅ Refresh every 3 h from the Mac (launchd `com.dallasreswatch.local`, all platforms). Fixed Nov 19 (silent exit bug).
- ✅ A failed check keeps the last good slots, shown faded as "older check".
- ✅ OpenTable rate-limit backoff.
- ⏳ Optional cloud schedule (GitHub Actions, Resy + SevenRooms only): needs `gh auth refresh -s workflow`.

### 1.3 Data: media
- 🔨 Each venue gets 1–5 **vibe photos** (dining room / bar / food), a **menu link** and the **official website**, stored in `media.json` (built by `media_build/merge_media.py` from `resy.json`, `ot.json`, `chrome.json`).
  - ✅ Resy venues (12) from Resy's API.
  - 🔨 OpenTable venues (24) via headless Chrome.
  - ⬜ Everything else via Claude in Chrome (official sites).

### 1.4 Page: layout & visuals
- ✅ Separate **Restaurants** and **Bars** sections (toggle Restaurants / Bars / Both).
- ✅ Card per venue: photo, Beli average in a coloured circle + rating count, Top-25 tag, cuisine · area · platform, short blurb, most-recommended dish chips.
- 🔨 Photo **carousel** per card (swipe + arrows + dots).
- 🔨 **Compact list view** toggle (one row per venue: thumb, score, 9-day open counts, Book button).
- ✅ Refined look: serif display headings, warm palette, sticky frosted toolbar.

### 1.5 Page: booking (must be obvious)
- ✅ Big primary button on every card: "Book on Resy / OpenTable / SevenRooms / Tock →", or "Call to book", "Walk-in only", "Closed".
- ✅ 9-day strip per card with the count of open times per day; tapping a day shows its times.
- ✅ **Every time is a button that deep-links** to that venue's booking page with date, time and party of 4 pre-filled.
- ✅ Secondary buttons: Menu · Site · Call.

### 1.6 Page: sorting & filtering
- 🔨 Sort: Beli score (default) · Most open tables · Soonest available · Top-25 rank · A–Z.
- 🔨 Filters: day, time of night (Any / Early 5–7 / Prime 7–8:30 / Late 8:30+), area, food type, "Open only", "Book online only", search (name, food, area, dish). "Reset" when any filter is on.
- 🔨 Numbering always = rank by Beli average within the section.
- ✅ Filters remembered per device (localStorage).

### 1.7 Acceptance
- Headless screenshot at desktop (1300px) and phone (390px) widths, light and dark: no broken images, no overlap, no sideways scroll.
- Deep links spot-checked for one venue per platform.
- Live at https://griffinw1.github.io/dallas-res-watch/site/ after push; the 3-hourly job keeps the new design (it runs `render.py`).

---

## Part 2 — Trip plan (`trip/`)

A **rough** plan, lighter than the Aspen itinerary: where things slot in, not a deep guide.
Owner: the "Dallas trip rough plan" session. Live at https://griffinw1.github.io/dallas-res-watch/trip/.

### 2.1 People
- ✅ Core: **Griffin, Lance, Saket**.
- ✅ Joining for parts: Griffin's sister Stella, Saket's sister, Griffin's parents, Saket's mom (+ others TBD). Name chips per item.

### 2.2 What's on the books (the only "booked" items)
- ✅ **Tue Nov 24, 7:30 PM: dinner for 8.** Griffin, Lance, Saket, Stella, Saket's sister, Griffin's parents, Saket's mom. Restaurant: **Casa Brasa** (Park Cities; linked to its Resy page).
- ✅ **Wed Nov 25, 7:45 PM: Tatsu, party of 4.** Griffin, Saket, Stella, Saket's sister.
  - ✅ Idea: pre-drinks at a bar ~5 PM.
  - ✅ Idea: club after, maybe Vice Park.

### 2.3 Plan structure
- ✅ Week at a glance + a section per day with morning / afternoon / evening slots, each marked **Booked / Idea / Open**.
- ✅ Possible **lakehouse** stretch for a few days (dates ❓), shown as a tentative block.
- ✅ Dinner ideas for open evenings pulled from Part 1's live data (`../results.json`, fetched on load): 3 places with tables for 4 that night, preferring a 6:00–8:30 slot, then Beli Top-25 rank. Notes that groups bigger than 4 should call.
  - ⏳ "Linking to the grid for that day": trip links to `../site/#d=YYYY-MM-DD`, but the grid doesn't read the hash yet, so it opens the full grid. Needs Part 1 to support `#d=`.
  - ⏳ Ranking uses Beli Top-25 rank because `results.json` has `beli_avg` for only 1 venue; will switch to averages once Part 1 writes them into `results.json`.
- ✅ "Open questions" list: where everyone stays, who joins when, Thanksgiving plans, lakehouse dates.

### 2.4 Acceptance
- ✅ Readable on a phone in one scroll per day; booked items stand out (green Booked pill); links to `../site/` work. Checked at 375px light/dark, no sideways scroll.

---

## Open questions for Griffin
1. Lakehouse: which days, and who's going?
2. Thanksgiving (Thu Nov 26): family plans?
3. Any other friends joining, and for which nights?
4. When can the Mac sit untouched for ~1 h (Beli scores)?
5. Where is everyone staying (neighborhood is enough), and does it change mid-week?
6. When do Lance and Saket land Fri, and when does everyone leave Sat Nov 28?
7. Wed night: which bar for ~5 PM pre-drinks, and is Vice Park the club (table or tickets needed)?
8. Which other nights want a dinner, and for how many?
9. Any must-dos (Cowboys Thanksgiving game, Mavericks, a big dinner to book ahead)? Car or rideshare?
