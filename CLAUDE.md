# Graybook Project

## Project Goal

Analyze the Nimitz Graybook (8-volume WWII operational diary) and build a "This Day in the Pacific War" dashboard showing the CINCPAC running summary for each date alongside a historian's interpretation.

## Current Status

**v1 is complete and running.** Open `3_Outputs/index.html` in a browser — no server needed. All 227 Vol. I entries (1941-12-07 to 1942-09-03) are navigable. OCR cleaning, narrative truncation, and quality auditing are complete.

---

## Folder Structure

```
1_Inputs/       reference design files (app.jsx, entries.js, tweaks-panel.jsx, HTML)
2_Scripts/      all scripts — see inventory below
3_Outputs/      production files served as the dashboard
docs/           audit reports and correction logs
```

---

## Scripts Inventory (2_Scripts/)

| Script | Purpose |
|---|---|
| `clean_ocr.py` | OCR-corrects raw JSON → `graybook_vol1_clean.json` |
| `build_entries.py` | Structures + truncates cleaned JSON → `entries.js` |
| `audit_entries.py` | Quality audit: before/after comparison of raw vs displayed entries |
| `extract_running_summary.py` | Original extraction from PDF OCR → `graybook_vol1.json` |
| `proxy.js` + `package.json` | Express proxy for live AI calls (not used in v1, kept for future) |
| `test_build_entries.py` | pytest tests for build_entries.py helpers (34 tests, all passing) |

---

## Data Pipeline

```
graybook_vol1.json          ← raw OCR extraction (extract_running_summary.py)
       ↓  clean_ocr.py
graybook_vol1_clean.json    ← conservative OCR corrections (3,340 fixes)
       ↓  build_entries.py
3_Outputs/entries.js        ← 227 structured, truncated, display-ready entries
```

### Step 1 — clean_ocr.py

Reads `graybook_vol1.json`, writes `graybook_vol1_clean.json`. Logs all changes to `docs/ocr_corrections.log`. Uses `/usr/share/dict/words` with suffix stripping (plurals, inflections) for word validation.

Rules (conservative — never modifies all-caps tokens like CINCPAC, USS):
1. Strip `~` and `\` embedded between alphanumeric chars
2. Remove spurious leading lowercase-l before capitals (`lJapanese → Japanese`) — only when the result is a valid word and not all-caps
3. Replace a single digit `1`/`0` flanked by letters with `l`/`I`/`O` when the result is a valid word
4. Replace `rn` → `m` when the result is a valid word (OCR misreads `m` as `rn`)
5. Rejoin line-break hyphens (`separa-ted → separated`) when the combined form is valid

Outcome: 3,340 substitutions across 189 of 227 entries. Transposition correction was evaluated and excluded — too many false positives on OCR fragments and inflected forms not in the system dictionary.

### Step 2 — build_entries.py

Reads `graybook_vol1_clean.json`, writes `3_Outputs/entries.js`.

Key behaviors:
- **`truncate_to_narrative()`** — many entries had absorbed appended documents (dispatch logs with `DD HHMM UNIT` format, strategic estimates, appendix sections). Truncates at the first structural boundary marker; hard cap of 1,000 words. 38 entries truncated; max dropped from 22,884 → 1,000 words.
- **`merge_fragments()`** — merges paragraph chunks that start with lowercase/comma, are <8 words, or where the previous chunk lacks terminal punctuation (`.?!`).
- **`has_ocr_garbage()`** — tags paragraphs `degraded: true` if they contain tildes, non-standard symbol clusters, or mixed-case OCR patterns (e.g. `\b[a-z][A-Z]`, `[A-Z]{2}\.?[a-z]`).
- **`extract_event()`** — conservative first-line extraction: requires ≥4 chars, starts with alpha, ≥60% alpha ratio, truncated to 60 chars.
- **Command derivation**: Kimmel ≤ 1941-12-30, Pye = 1941-12-31, Nimitz ≥ 1942-01-01.
- **`place`** is always `""` — no reliable geographic signal in the OCR text.

### Entry schema (entries.js)

```js
window.WAR_TIMELINE = { start: "1941-12-07", end: "1942-09-03" };
window.ENTRIES = [
  {
    date:    "1942-06-04",
    event:   "Forewarned by his codebreakers, Nimitz knew",  // first clean line, or ""
    place:   "",
    command: "ADM. C. W. NIMITZ, CINCPAC",
    actual:  [{ text: "...", degraded: false }, ...],
    note:    { knew: "...", didntKnow: "...", coming: "..." }
  },
  ...
]
```

- `actual[].degraded` → renders muted at 45% opacity with *[transmission degraded]* marker
- `note` has real historian prose for 5 key dates; all others have a placeholder in `knew` only
- `note.didntKnow` and `note.coming` are `""` for placeholder entries — NotePanel skips empty sections

---

## Dashboard Files (3_Outputs/)

| File | Role |
|---|---|
| `index.html` | **Generated — do not edit directly.** Self-contained HTML. |
| `entries.js` | **Generated.** 227 entries as `window.ENTRIES`. |
| `app.jsx` | React app source. Edit this, then rebuild index.html. |
| `tweaks-panel.jsx` | UI controls shell. Copied verbatim from `1_Inputs/`. |
| `graybook_vol1_clean.json` | OCR-corrected source data. |
| `graybook_vol1.json` | Original raw OCR output. |

### Why index.html inlines the JSX

The HTML loads React from CDN and compiles JSX in-browser via Babel standalone. Babel's `<script type="text/babel" src="...">` uses XHR to fetch the file — which Chrome blocks from `file://` URLs. Inlining the JSX into `<script type="text/babel">` blocks avoids this. Only `entries.js` stays external (plain `<script src>` tags work fine from `file://`).

### How to rebuild index.html

Run this from the project root after editing `app.jsx` or `tweaks-panel.jsx`:

```python
python3 -c "
import pathlib, re

root   = pathlib.Path('.')
tweaks = (root / '3_Outputs/tweaks-panel.jsx').read_text()
app    = (root / '3_Outputs/app.jsx').read_text()
ref    = (root / '1_Inputs/This Day in the Pacific War.html').read_text()
css    = re.search(r'<style>(.*?)</style>', ref, re.DOTALL).group(1)

extra = '''
  .hdr { z-index: 2; }
  .hdr-sub { font-size: 9px; letter-spacing: 0.18em; white-space: nowrap; }
  .typed-p { word-wrap: break-word; overflow-wrap: break-word; }
  .typed-p-degraded { opacity: 0.45; }
  .ocr-marker {
    font-size: 9.5px; letter-spacing: 0.14em; font-weight: 500;
    color: var(--ink-faint); margin-left: 8px;
    font-family: var(--font-ui); font-style: italic;
    vertical-align: middle;
  }
  .cal-nav-group { display: flex; gap: 2px; }
'''

html = ('<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\" />\n'
        '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />\n'
        '<title>This Day in the Pacific War</title>\n'
        '<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />\n'
        '<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />\n'
        '<link href=\"https://fonts.googleapis.com/css2?family=Courier+Prime:ital,wght@0,400;0,700;1,400&family=IBM+Plex+Sans:wght@300;400;500;600;700&family=Spectral:ital,wght@0,400;0,500;0,600;1,400&display=swap\" rel=\"stylesheet\" />\n'
        '<style>' + css + extra + '</style>\n</head>\n<body>\n  <div id=\"root\"></div>\n'
        '  <script src=\"https://unpkg.com/react@18.3.1/umd/react.development.js\" integrity=\"sha384-hD6/rw4ppMLGNu3tX5cjIb+uRZ7UkRJ6BPkLpg4hAu/6onKUg4lLsHAs9EBPT82L\" crossorigin=\"anonymous\"></script>\n'
        '  <script src=\"https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js\" integrity=\"sha384-u6aeetuaXnQ38mYT8rp6sbXaQe3NL9t+IBXmnYxwkUI2Hw4bsp2Wvmx4yRQF1uAm\" crossorigin=\"anonymous\"></script>\n'
        '  <script src=\"https://unpkg.com/@babel/standalone@7.29.0/babel.min.js\" integrity=\"sha384-m08KidiNqLdpJqLq95G/LEi8Qvjl/xUYll3QILypMoQ65QorJ9Lvtp2RXYGBFj1y\" crossorigin=\"anonymous\"></script>\n'
        '  <script src=\"entries.js\"></script>\n'
        '  <script type=\"text/babel\">\n' + tweaks + '\n  </script>\n'
        '  <script type=\"text/babel\">\n' + app + '\n  </script>\n</body>\n</html>')

out = root / '3_Outputs/index.html'
out.write_text(html)
c = out.read_text()
assert 'p.degraded' in c and 'cal-nav-group' in c
print('OK —', len(html), 'chars')
"
```

Verify with: `assert 'p.degraded' in c and 'cal-nav-group' in c` — if either is missing, the inlining failed silently.

---

## app.jsx Design Decisions

The production `app.jsx` diverges from the `1_Inputs/` reference in four ways:

1. **No live AI** — `HAS_AI`, `callHistorian`, `aiCache`, `runGenerate`, and the auto-generate `useEffect` are all removed. Notes are static (pre-written or placeholder).
2. **NotePanel simplified** — no status chip logic, no regenerate button, no loading skeleton. Renders `entry.note` directly. Skips empty `didntKnow`/`coming` sections (placeholder entries).
3. **Drop cap gated** — `note-lead` class (which triggers the serif drop cap) only applied when all three note fields are populated (`isReal = !!(knew && didntKnow && coming)`).
4. **`actual` format** — paragraphs are `{text, degraded}` objects, not strings. `ActualPanel` renders degraded paragraphs at reduced opacity with an `[transmission degraded]` marker.

---

## Dashboard UI Features

- **Navigation**: left/right arrow buttons, keyboard ← → arrows, calendar popover
- **Calendar**: stepped pagination — `‹`/`›` = 1 month, `«`/`»` = 1 year; year arrows clamp to timeline boundaries
- **Timeline**: bottom bar shows progress from Pearl Harbor to Sep 1942; clickable dot markers for all 227 entries
- **Tweaks panel**: activated by `__activate_edit_mode` postMessage — font, grain, accent color, marker toggle (not available in plain file:// mode without the host app)
- **localStorage**: saves current entry index across page loads (`tdpw_index`)

---

## Historian's Notes

Five dates have hand-written three-paragraph notes (WHAT HE KNEW / WHAT HE DIDN'T YET KNOW / WHAT WAS COMING):
- 1941-12-07 — Pearl Harbor (Kimmel)
- 1941-12-31 — Nimitz takes command, Pye handover
- 1942-05-25 — Midway lead-up (Nimitz)
- 1942-06-04 — Battle of Midway (Nimitz)
- 1942-08-07 — Guadalcanal landings (Nimitz)

All other entries show: *"Historian's Note coming soon. This entry covers [date]. The full AI interpretation feature will be enabled in a future version."*

The live-AI path (proxy.js + Anthropic API) exists but is not wired in v1. System prompt is hardcoded server-side in `proxy.js` — the three-paragraph structure, historian's voice, and Kimmel/Nimitz distinction never go to the client.

---

## Quality Audit (audit_entries.py)

Reads raw JSON and entries.js, compares before/after on three flags:
- `ocr_score > 5` — embedded symbols, digit substitutions, garbled alphanumeric runs
- `too_short < 100 words`
- `frag_paras > 30%` paragraphs under 10 words

**Final state after all fixes:**

| | Raw JSON | Displayed (entries.js) |
|---|---|---|
| Clean (0 flags) | 25 (11%) | **115 (51%)** |
| Minor issues (1–2 flags) | 202 (89%) | 112 (49%) |
| Significant (3+ flags) | 0 | 0 |
| Avg words/entry | 1,040 | 319 |
| Median words/entry | 264 | 245 |
| Max words/entry | 22,884 | 1,000 |

Full report: `docs/entry_audit.txt` | OCR correction log: `docs/ocr_corrections.log`

---

## Vol. I Extraction Status

- Script: `2_Scripts/extract_running_summary.py`
- Raw output: `3_Outputs/graybook_vol1.json` — 227 entries, 1941-12-07 to 1942-09-03
- Known gaps:
  - Midway gap (May 23–Jun 2, except May 25): suspicious — needs raw page dump to investigate
  - Other gaps assumed genuine (no entry in the document)
  - Many long entries had absorbed appended documents (dispatch logs, strategic estimates) — now handled by `truncate_to_narrative()` in build_entries.py

---

## What's Next (potential)

- Add more hand-written historian notes (currently only 5 of 227)
- Wire live AI via `proxy.js` when Anthropic API access is available
- Investigate the Midway gap (May 23–Jun 2) in the raw PDF
- Extend to Vol. II and beyond
- Improve `place` field extraction (currently always blank)
