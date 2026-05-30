import pdfplumber
import re
import json
from datetime import datetime

PDF_PATH = "1_Inputs/Nimitz_Graybook Volume 1.pdf"
OUTPUT_PATH = "3_Outputs/graybook_vol1.json"

MONTH_NUMS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'decenber': 12,  # OCR variant on page 4
}

# Handles all observed date-header variants:
#   "December 7 -"   "December 8."   "May 23."
#   "May 24"  "MAY 30"  (bare, no punctuation)
#   "May 29th (cont'd)"  (ordinal + continuation marker)
DATE_RE = re.compile(
    r'^(January|February|March|April|May|June|July|August'
    r'|September|October|November|December|Decenber)\s+(\d{1,2})'
    r'(?:st|nd|rd|th)?'            # optional ordinal suffix
    r'(?:'
        r'\s*[.\-]'                # period or dash (body text may follow)
        r'|\s*\(Cont[^)]*\)?'      # "(cont'd)" continuation marker
        r'|\s*$'                   # bare date, nothing after
    r')',
    re.IGNORECASE
)

SUMMARY_HEADER_RE = re.compile(r'RUNNING\s+SUMMARY\s+OF\s+SITUATION', re.IGNORECASE)
FUZZY_SUMMARY_RE  = re.compile(
    r'(?=.*(?:RUNN|RUYIJ))(?=.*(?:SUMM|SUI\\.))(?=.*SITU)',
    re.IGNORECASE
)
DIRECTIVES_RE = re.compile(r'DIRECTIVES\s+AND\s+INFORMATION\s+AFFECTING', re.IGNORECASE)
PAGE_NUM_RE   = re.compile(r'^\s*-?\d{1,3}-?\s*$')

entries: dict[str, list[str]] = {}
current_key: str | None = None
current_lines: list[str] = []
in_summary = True   # page 4 is always narrative; start True
current_year = 1941
last_month: int | None = None


def flush():
    global current_key, current_lines
    if current_key and current_lines:
        text = '\n'.join(current_lines).strip()
        if text:
            entries.setdefault(current_key, [])
            entries[current_key].append(text)
    current_lines = []


with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_num <= 3:
            continue

        raw = page.extract_text()
        if not raw:
            continue

        for line in raw.split('\n'):
            stripped = line.strip()

            # Exit narrative on directives header
            if DIRECTIVES_RE.search(stripped):
                flush()
                in_summary = False
                continue

            # Re-enter on exact or fuzzy summary header
            if SUMMARY_HEADER_RE.search(stripped):
                in_summary = True
                continue
            if not in_summary and FUZZY_SUMMARY_RE.search(stripped):
                in_summary = True
                continue

            # Skip bare page numbers regardless of section
            if PAGE_NUM_RE.match(stripped):
                continue

            # Date anchor?
            m = DATE_RE.match(stripped)
            if m:
                flush()
                in_summary = True   # Fix: date anchor always means narrative section

                month_name = m.group(1).lower()
                month_num  = MONTH_NUMS[month_name]
                day        = int(m.group(2))

                if last_month == 12 and month_num == 1:
                    current_year += 1
                last_month = month_num

                try:
                    current_key = datetime(current_year, month_num, day).strftime('%Y-%m-%d')
                except ValueError:
                    current_key = None
                    continue

                # Any text after the date marker on the same line is body text
                rest = stripped[m.end():].strip()
                if rest:
                    current_lines.append(rest)

            elif current_key and in_summary:
                # Only accumulate when in narrative section — prevents
                # dispatches text leaking into entries when in_summary=False
                # but current_key is still set from a prior narrative date.
                current_lines.append(line.rstrip())

flush()

output = {k: '\n\n'.join(v) for k, v in entries.items()}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# ── Validation summary ──────────────────────────────────────────────────────
dates = sorted(datetime.strptime(d, '%Y-%m-%d') for d in output)

print(f"Total entries : {len(dates)}")
if dates:
    print(f"First date    : {dates[0].strftime('%Y-%m-%d')}")
    print(f"Last date     : {dates[-1].strftime('%Y-%m-%d')}")

    gaps = []
    for a, b in zip(dates, dates[1:]):
        delta = (b - a).days
        if delta > 4:
            gaps.append((a, b, delta - 1))

    if gaps:
        print(f"\nGaps > 3 consecutive days ({len(gaps)} found):")
        for start, end, missing in gaps:
            print(f"  {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}  ({missing} days missing)")
    else:
        print("\nNo gaps longer than 3 consecutive days.")
