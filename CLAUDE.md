# Graybook Project

## Agent Behavior

Do not load planning skills, subagents, or orchestration frameworks.
Implement directly in a single session. No API calls in scripts.

## Project Goal

Analyze the Nimitz Graybook (8-volume WWII operational diary) and build a "This Day in the Pacific War" dashboard showing the CINCPAC running summary for each date alongside a historian's interpretation.

## Current Status

**v1 is complete and live at https://graybook-lemon.vercel.app/** (auto-deploys from `main`). All 227 Vol. I entries (1941-12-07 to 1942-09-03) are navigable. OCR cleaning, narrative truncation, quality auditing, page-number extraction, and citation UI are complete.

**UI state (2026-05-31):** Both panels have `border: 1px solid var(--line)`, `border-radius: 4px`, `overflow: hidden`. Citation bar reads "SOURCE — NIMITZ GRAYBOOK VOL. I · p. N" on both panels (right panel hidden via `visibility: hidden` until dispatches are wired). Timeline marker: `top: -8px` (clears tick labels), flag centered (no `translateX` offset).

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
| `extract_running_summary.py` | Extraction from PDF OCR → `graybook_vol1.json` |
| `clean_ocr.py` | OCR-corrects raw JSON → `graybook_vol1_clean.json` |
| `build_entries.py` | Structures + truncates cleaned JSON → `entries.js` |
| `audit_entries.py` | Quality audit: before/after comparison of raw vs displayed entries |
| `1_Investigation Scripts/flag_ocr.py` | OCR flag investigation script |
| `2_Tests/test_build_entries.py` | pytest tests for build_entries.py helpers (34 tests, all passing) |
| `2_Tests/test_clean_ocr.py` | pytest tests for clean_ocr.py |
| `3_Proxy/proxy.js` + `package.json` | Express proxy for live AI calls (not used in v1, kept for future) |

**Dependency:** `pdfplumber` is required for `extract_running_summary.py`. Install with `pip3 install pdfplumber` if missing. Scripts are Python 3.9+ compatible.

---

## Data Pipeline

```
graybook_vol1.json          ← raw OCR extraction (extract_running_summary.py)
       ↓  clean_ocr.py
graybook_vol1_clean.json    ← conservative OCR corrections (3,756 fixes across 208 entries)
       ↓  build_entries.py
3_Outputs/entries.js        ← 227 structured, truncated, display-ready entries
```

**JSON format:** Both `graybook_vol1.json` and `graybook_vol1_clean.json` use `{"date": {"text": "...", "page": N}}` — not flat strings. The `page` field is the PDF page where that date entry begins (first occurrence wins).

### Step 1 — extract_running_summary.py

Reads `1_Inputs/Nimitz_Graybook Volume 1.pdf`, writes `graybook_vol1.json`. Tracks the PDF page number for each date entry.

### Step 2 — clean_ocr.py

Reads `graybook_vol1.json`, writes `graybook_vol1_clean.json`. Logs all changes to `docs/ocr_corrections.log`. Uses `/usr/share/dict/words` with suffix stripping for word validation. Passes the `page` field through unchanged.

Rules (conservative — never modifies all-caps tokens like CINCPAC, USS):
1. Strip `~` and `\` embedded between alphanumeric chars
2. Remove spurious leading lowercase-l before capitals (`lJapanese → Japanese`)
3. Replace a single digit `1`/`0` flanked by letters with `l`/`I`/`O` when the result is a valid word
4. Replace `rn` → `m` when the result is a valid word (OCR misreads `m` as `rn`)
5. Rejoin line-break hyphens (`separa-ted → separated`) when the combined form is valid

Transposition correction was evaluated and excluded — too many false positives on OCR fragments and inflected forms not in the system dictionary.

### Step 3 — build_entries.py

Reads `graybook_vol1_clean.json`, writes `3_Outputs/entries.js`.

Key behaviors:
- **Truncation** — entries absorbing dispatch logs, strategic estimates, and appendix sections are cut at the first structural boundary marker; hard cap of 1,000 words. 38 entries truncated; max dropped from 22,884 → 1,000 words.
- **Fragment merging** — paragraph chunks starting lowercase/comma, under 8 words, or following a chunk without terminal punctuation are merged into the previous paragraph.
- **Degraded tagging** — paragraphs with tildes, non-standard symbol clusters, or mixed-case OCR patterns are tagged `degraded: true` and rendered at reduced opacity with a `[transmission degraded]` marker.
- **Command derivation** — Kimmel ≤ 1941-12-30, Pye = 1941-12-31, Nimitz ≥ 1942-01-01.
- **`place`** is always `""` — no reliable geographic signal in the OCR text.

### Entry schema (entries.js)

```js
window.WAR_TIMELINE = { start: "1941-12-07", end: "1942-09-03" };
window.ENTRIES = [
  {
    date:    "1942-06-04",
    event:   "Forewarned by his codebreakers, Nimitz knew",  // first clean line, or ""
    place:   "",
    page:    42,                                              // PDF page number
    command: "ADM. C. W. NIMITZ, CINCPAC",
    actual:  [{ text: "...", degraded: false }, ...],
    note:    { knew: "...", didntKnow: "...", coming: "..." }
  },
  ...
]
```

- `note.didntKnow` and `note.coming` are `""` for placeholder entries — NotePanel skips empty sections

---

## Dashboard Files (3_Outputs/)

| File | Role |
|---|---|
| `index.html` | **Edit directly.** Self-contained HTML with all JSX inlined. Source of truth for the UI. |
| `entries.js` | **Generated** by `build_entries.py`. 227 entries as `window.ENTRIES`. |
| `app.jsx` | Legacy JSX source — **do not use to rebuild**; `index.html` has diverged. |
| `tweaks-panel.jsx` | Legacy UI controls shell — same caveat as `app.jsx`. |
| `graybook_vol1_clean.json` | OCR-corrected source data. |
| `graybook_vol1.json` | Original raw OCR output. |

### Why index.html inlines the JSX

The HTML loads React from CDN and compiles JSX in-browser via Babel standalone. Babel's `<script type="text/babel" src="...">` uses XHR to fetch the file — which Chrome blocks from `file://` URLs. Inlining the JSX into `<script type="text/babel">` blocks avoids this. Only `entries.js` stays external (plain `<script src>` tags work fine from `file://`).

> **Warning:** The old rebuild script (assembling from `app.jsx` + `1_Inputs/This Day in the Pacific War.html`) is now stale — running it would overwrite all CSS and UI changes made directly to `index.html` since 2026-05-31. Do not run it.

---

## Historian's Notes

Five dates have hand-written three-paragraph notes (WHAT HE KNEW / WHAT HE DIDN'T YET KNOW / WHAT WAS COMING):
- 1941-12-07 — Pearl Harbor (Kimmel)
- 1941-12-31 — Nimitz takes command, Pye handover
- 1942-05-25 — Midway lead-up (Nimitz)
- 1942-06-04 — Battle of Midway (Nimitz)
- 1942-08-07 — Guadalcanal landings (Nimitz)

All other entries show a placeholder in `knew` only; `didntKnow` and `coming` are empty strings.

---

## Quality Audit (audit_entries.py)

Reads raw JSON and entries.js, compares before/after on three flags:
- `ocr_score > 5` — embedded symbols, digit substitutions, garbled alphanumeric runs
- `too_short < 100 words`
- `frag_paras > 30%` paragraphs under 10 words

**Current state:**

| | Raw JSON | Displayed (entries.js) |
|---|---|---|
| Clean (0 flags) | 23 (10%) | **115 (51%)** |
| Minor issues (1–2 flags) | 204 (90%) | 112 (49%) |
| Significant (3+ flags) | 0 | 0 |
| Avg words/entry | 1,040 | 323 |
| Median words/entry | 264 | 245 |
| Max words/entry | 22,884 | 1,000 |

Full report: `docs/entry_audit.txt` | OCR correction log: `docs/ocr_corrections.log`

---

## Vol. I Extraction Status

- 227 entries, 1941-12-07 to 1942-09-03
- Only gap > 3 days: Aug 15–20 (4 days missing) — assumed genuine

---

## What's Next (potential)

- Add more hand-written historian notes (currently only 5 of 227)
- Wire live AI via `proxy.js` when Anthropic API access is available
- Extend to Vol. II and beyond
- Improve `place` field extraction (currently always blank)
