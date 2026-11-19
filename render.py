#!/usr/bin/env python3
"""results.json -> site/index.html (self-contained, no external deps).

  python3 render.py [--in results.json] [--out site/index.html]
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATFORM_LABEL = {"resy": "Resy", "opentable": "OpenTable", "sevenrooms": "SevenRooms", "tock": "Tock",
                  "phone": "Phone", "walkin": "Walk-in", "unknown": "?"}

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1f;--soft:#5f6368;--line:#e3e3df;--open:#0b7a4b;--openbg:#e6f4ec;
--err:#b3261e;--chip:#eef1f4;--accent:#1f4d8f}
@media (prefers-color-scheme:dark){:root{--bg:#121315;--card:#1b1c1f;--ink:#ececec;--soft:#a0a4a8;--line:#2c2e33;
--open:#5fd39a;--openbg:#143325;--err:#ff8a80;--chip:#262a30;--accent:#8ab4f8}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.4 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:16px 16px 8px;max-width:1400px;margin:auto}h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--soft);font-size:13px}.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0 4px}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{border:0;background:var(--card);color:var(--ink);padding:7px 12px;font:inherit;cursor:pointer}
.seg button.on{background:var(--accent);color:#fff}label.chk{display:inline-flex;gap:6px;align-items:center;
padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);cursor:pointer}
.wrap{overflow-x:auto;max-width:1400px;margin:8px auto 24px;padding:0 16px}
table{border-collapse:separate;border-spacing:0;background:var(--card);border:1px solid var(--line);border-radius:10px;min-width:100%}
th,td{border-bottom:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}
thead th{position:sticky;top:0;background:var(--card);font-size:12px;color:var(--soft);white-space:nowrap;z-index:1}
th.v,td.v{position:sticky;left:0;background:var(--card);z-index:2;min-width:170px;max-width:220px;border-right:1px solid var(--line)}
thead th.v{z-index:3}td.v a{color:var(--ink);font-weight:600;text-decoration:none}td.v a:hover{text-decoration:underline}
.meta{color:var(--soft);font-size:12px;margin-top:2px}.beli{display:inline-block;min-width:30px;text-align:center;
border-radius:999px;background:var(--chip);font-weight:600;font-size:12px;padding:1px 6px;margin-right:4px}
td.c{min-width:92px}td.c.has{background:var(--openbg)}.t{display:inline-block;background:var(--card);color:var(--open);
border:1px solid var(--open);border-radius:6px;padding:0 5px;margin:0 3px 3px 0;font-size:12px;white-space:nowrap;font-variant-numeric:tabular-nums}
.dash{color:var(--soft)}.note{color:var(--soft);font-style:italic;font-size:12px}.e{color:var(--err);font-size:12px;cursor:help}
tr.hide{display:none}footer{max-width:1400px;margin:0 auto 32px;padding:0 16px;color:var(--soft);font-size:12px}
@media (max-width:600px){th.v,td.v{min-width:130px;max-width:150px}td.c{min-width:80px}}
"""

JS = """
const rows=[...document.querySelectorAll('tbody tr')];let kind='all';
function apply(){const only=document.getElementById('only').checked;let n=0;
 rows.forEach(r=>{const ok=(kind==='all'||r.dataset.kind===kind)&&(!only||r.dataset.open==='1');r.classList.toggle('hide',!ok);if(ok)n++;});
 document.getElementById('count').textContent=n+' shown';
 try{localStorage.setItem('drw',JSON.stringify({kind,only}))}catch(e){}}
document.querySelectorAll('.seg button').forEach(b=>b.onclick=()=>{kind=b.dataset.k;
 document.querySelectorAll('.seg button').forEach(x=>x.classList.toggle('on',x===b));apply();});
document.getElementById('only').onchange=apply;
try{const s=JSON.parse(localStorage.getItem('drw')||'{}');if(s.kind){kind=s.kind;
 document.querySelectorAll('.seg button').forEach(x=>x.classList.toggle('on',x.dataset.k===kind));}
 if(s.only)document.getElementById('only').checked=true;}catch(e){}
apply();
"""


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def col_label(d: str) -> str:
    x = dt.date.fromisoformat(d)
    return f"{x:%a} {x.month}/{x.day}"


def cell(v: dict, d: str) -> tuple[str, bool]:
    st = v.get("status", {}).get(d, "")
    slots = v.get("slots", {}).get(d, [])
    note = (v.get("day_notes") or {}).get(d)
    if st == "skipped":
        reason = v.get("skip_reason") or note or "skipped"
        if (v.get("notes") or "").startswith("CLOSED"):
            reason = "closed"
        if reason == "call" and v.get("phone"):
            return f'<a class="note" href="tel:{esc(v["phone"])}">call</a>', False
        return f'<span class="note">{esc(reason)}</span>', False
    if st.startswith("error"):
        return f'<span class="e" title="{esc(st)}">error</span>', False
    if slots and note and note.startswith("stale"):
        return (f'<div title="{esc(note)}" style="opacity:.55">' + "".join(
            f'<span class="t">{esc(t.replace(" PM", "p").replace(" AM", "a"))}</span>' for t in slots)
            + '<div class="note">older check</div></div>'), True
    if slots:
        return "".join(f'<span class="t">{esc(t.replace(" PM", "p").replace(" AM", "a"))}</span>' for t in slots), True
    return f'<span class="dash" title="{esc(note or "no open slots in window")}">—</span>', False


def sort_key(v: dict):
    r = v.get("beli_rank")
    b = v.get("beli_avg")
    return (r is None, r or 0, b is None, -(b or 0), v["name"].lower())


def render(res: dict) -> str:
    dates = res["dates"]
    gen = dt.datetime.fromisoformat(res["generated_at"])
    win = res.get("window", {})
    venues = sorted(res["venues"], key=sort_key)
    body = []
    for v in venues:
        cells, any_open = [], False
        for d in dates:
            c, has = cell(v, d)
            any_open |= has
            cells.append(f'<td class="c{" has" if has else ""}">{c}</td>')
        name = esc(v["name"])
        link = f'<a href="{esc(v["url"])}" target="_blank" rel="noopener">{name}</a>' if v.get("url") else f"<b>{name}</b>"
        beli = f'<span class="beli" title="Beli avg ({esc(v.get("beli_ratings") or "?")} ratings)">{v["beli_avg"]:.1f}</span>' \
            if isinstance(v.get("beli_avg"), (int, float)) else ""
        checked = v.get("checked_at", "")
        rank = f'<span class="beli" title="Beli Top 25 Restaurants in Dallas">#{v["beli_rank"]}</span> ' if v.get("beli_rank") else ""
        meta = f'{rank}{beli}{esc(v.get("kind") or "")} · {esc(PLATFORM_LABEL.get(v.get("platform"), v.get("platform")))}{(" · " + esc(v["hood"])) if v.get("hood") else ""}'
        body.append(f'<tr data-kind="{esc(v.get("kind") or "restaurant")}" data-open="{int(any_open)}">'
                    f'<td class="v" title="checked {esc(checked)}">{link}<div class="meta">{meta}</div></td>{"".join(cells)}</tr>')
    head = "".join(f"<th>{col_label(d)}</th>" for d in dates)
    start = win.get("start", "17:00")
    end = win.get("end", "22:00")
    fmt = lambda s: dt.datetime.strptime(s, "%H:%M").strftime("%-I:%M %p")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Dallas Tables</title>
<style>{CSS}</style></head><body>
<header><h1>Dallas tables · party of {res.get("party", 4)}</h1>
<div class="sub">Open reservation times {fmt(start)}–{fmt(end)} Central, {col_label(dates[0])} – {col_label(dates[-1])}.
Last updated <b>{gen:%a %b %-d, %-I:%M %p} CT</b>. Read-only. Tap a name to book on the restaurant's page.</div>
<div class="controls"><div class="seg"><button data-k="all" class="on">All</button><button data-k="restaurant">Restaurants</button>
<button data-k="bar">Bars</button></div><label class="chk"><input type="checkbox" id="only"> Only with openings</label>
<span class="sub" id="count"></span></div></header>
<div class="wrap"><table><thead><tr><th class="v">Venue (by Beli)</th>{head}</tr></thead>
<tbody>{"".join(body)}</tbody></table></div>
<footer>— none in window · "call" / "walk-in" = no online booking · "error" = check failed (hover for details).
Each row's last check time is in its tooltip. Slots can disappear quickly; confirm on the booking page.</footer>
<script>{JS}</script></body></html>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(HERE / "results.json"))
    ap.add_argument("--out", default=str(HERE / "site" / "index.html"))
    a = ap.parse_args()
    res = json.loads(Path(a.inp).read_text())
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(res))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
