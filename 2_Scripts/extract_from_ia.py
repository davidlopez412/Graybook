import json
import re
from datetime import datetime
from xml.etree.ElementTree import iterparse

XML_PATH = "1_Inputs/NimitzGraybookVolume1Of87December1941-31August1942_djvu.xml"
PAGE_NUMS_PATH = "1_Inputs/NimitzGraybookVolume1Of87December1941-31August1942_page_numbers.json"
OUTPUT_PATH = "3_Outputs/graybook_vol1.json"
CUTOFF = datetime(1941, 12, 7)

MONTH_NUMS = {
    # Standard spellings
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    # Carry-over variant from PDF extractor
    'decenber': 12,
    # User-specified IA OCR variants
    'dece::iber': 12, 'deceiber': 12,
    'hay': 5, 'kay': 5,
    # Discovered from IA XML scan
    'anril': 4,       # April: 'p' misread as 'n'
    'jure': 6,        # June: 'n' misread as 'r'
    'jul?': 7,        # July: 'y' misread as '?'
    'ma?': 5,         # May: 'y' misread as '?'
    'auptust': 8,     # August: garbled scan
    'aiig-ust': 8,    # August: garbled scan
    'au~ust': 8,      # August: garbled scan
}

# Copied verbatim from extract_running_summary.py
DATE_RE = re.compile(
    r'^(January|February|March|April|May|June|July|August'
    r'|September|October|November|December|Decenber)\s+(\d{1,2})'
    r'(?:st|nd|rd|th)?'
    r'(?:\s*[.\-]|\s*\(Cont[^)]*\)?|\s*$)',
    re.IGNORECASE
)

# Validates what follows month+day in a fuzzy match (same rules as DATE_RE,
# but without a trailing $ so body text after a period is allowed)
FUZZY_SUFFIX_RE = re.compile(
    r'^(?:st|nd|rd|th)?(?:\s*[.\-]|\s*\(Cont[^)]*\)?|\s*$)',
    re.IGNORECASE
)


def parse_page_num(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def try_fuzzy_date(line):
    """
    Secondary date detection for lines DATE_RE couldn't match.
    Handles garbled month names and the G-as-6 OCR substitution.
    Returns (month_num, day, rest_text) or None.
    """
    stripped = line.strip()
    tokens = stripped.split()
    if len(tokens) < 2:
        return None

    first_lower = tokens[0].lower()

    # Exact key match first; then substring for keys >= 5 chars (avoids
    # false positives from short keys like 'may' matching 'maylander')
    month_num = MONTH_NUMS.get(first_lower)
    if month_num is None:
        for key, num in MONTH_NUMS.items():
            if len(key) >= 5 and key in first_lower:
                month_num = num
                break
    if month_num is None:
        return None

    raw_day = tokens[1]
    if raw_day.upper() == 'G':
        day = 6
        after_day = stripped[len(tokens[0]):].lstrip()[len(raw_day):]
    else:
        m = re.match(r'^(\d{1,2})(.*)', raw_day)
        if not m:
            return None
        day = int(m.group(1))
        after_tok1 = stripped[len(tokens[0]):].lstrip()[len(raw_day):]
        after_day = m.group(2) + after_tok1

    if not (1 <= day <= 31):
        return None

    sm = FUZZY_SUFFIX_RE.match(after_day)
    if sm is None:
        return None

    rest = after_day[sm.end():].strip()
    return month_num, day, rest


# ── Load page numbers ─────────────────────────────────────────────────────────
with open(PAGE_NUMS_PATH, encoding='utf-8') as f:
    pn_data = json.load(f)

leaf_to_page = {
    entry['leafNum'] - 1: parse_page_num(entry.get('pageNumber', ''))
    for entry in pn_data['pages']
}

# ── Load PDF fallback BEFORE overwriting the output file ─────────────────────
try:
    with open(OUTPUT_PATH, encoding='utf-8') as f:
        pdf_fallback = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pdf_fallback = {}

# ── State ─────────────────────────────────────────────────────────────────────
entries = {}
current_key = None
pending_lines = []
current_year = 1941
last_month = None


def handle_date_match(month_num, day, rest, printed_page):
    global current_key, pending_lines, current_year, last_month

    if current_key is not None and pending_lines:
        text = '\n'.join(pending_lines).strip()
        if text:
            entries[current_key]['chunks'].append(text)
    pending_lines = []

    if last_month == 12 and month_num == 1:
        current_year += 1
    last_month = month_num

    try:
        current_key = datetime(current_year, month_num, day).strftime('%Y-%m-%d')
    except ValueError:
        current_key = None
        return

    if current_key not in entries:
        entries[current_key] = {'chunks': [], 'page': printed_page}

    if rest:
        pending_lines.append(rest)


def process_page(page_lines, printed_page):
    for line in page_lines:
        stripped = line.strip()
        if not stripped:
            continue

        m = DATE_RE.match(stripped)
        if m:
            handle_date_match(
                MONTH_NUMS[m.group(1).lower()],
                int(m.group(2)),
                stripped[m.end():].strip(),
                printed_page,
            )
        else:
            fuzzy = try_fuzzy_date(stripped)
            if fuzzy:
                handle_date_match(*fuzzy, printed_page)
            elif current_key is not None:
                pending_lines.append(line.rstrip())


# ── Stream-parse XML ──────────────────────────────────────────────────────────
leaf_idx = -1
cur_words = []
cur_page_lines = []

for event, elem in iterparse(XML_PATH, events=('start', 'end')):
    if event == 'start' and elem.tag == 'OBJECT':
        leaf_idx += 1
        cur_words = []
        cur_page_lines = []
    elif event == 'end':
        if elem.tag == 'WORD':
            word = (elem.text or '').strip()
            if word:
                cur_words.append(word)
            elem.clear()
        elif elem.tag == 'LINE':
            if cur_words:
                cur_page_lines.append(' '.join(cur_words))
                cur_words = []
            elem.clear()
        elif elem.tag == 'OBJECT':
            process_page(cur_page_lines, leaf_to_page.get(leaf_idx))
            elem.clear()

# Final flush
if current_key is not None and pending_lines:
    text = '\n'.join(pending_lines).strip()
    if text:
        entries[current_key]['chunks'].append(text)

# ── Build IA output ───────────────────────────────────────────────────────────
output = {}
for k, v in sorted(entries.items()):
    if v['chunks']:
        output[k] = {
            'text': '\n\n'.join(v['chunks']),
            'page': v['page'],
            'source': 'ia',
        }

# Fix: 1941-12-03 is a misread of December 8 (OCR read '8' as '3')
if '1941-12-03' in output:
    if '1941-12-08' not in output:
        output['1941-12-08'] = output.pop('1941-12-03')
    else:
        del output['1941-12-03']  # Dec 8 already present; discard the duplicate

# Pre-Dec-7 warnings (after rename, so Dec 8 no longer appears here)
early_warnings = [
    (k, output[k]['page'], output[k]['text'][:100])
    for k in output
    if datetime.strptime(k, '%Y-%m-%d') < CUTOFF
]

# ── Merge PDF fallback for any dates missing from IA ─────────────────────────
fallback_dates = sorted(set(pdf_fallback.keys()) - set(output.keys()))
for date in fallback_dates:
    entry = dict(pdf_fallback[date])
    entry['source'] = 'pdf_fallback'
    output[date] = entry

output = dict(sorted(output.items()))

# ── Write combined output ─────────────────────────────────────────────────────
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# ── Pre-Dec-7 warnings ────────────────────────────────────────────────────────
if early_warnings:
    print(f"WARNING: {len(early_warnings)} date(s) before 1941-12-07 (review manually):")
    for date, page, preview in early_warnings:
        print(f"  {date} (p.{page}): {preview!r}")
    print()

# ── PDF fallback report ───────────────────────────────────────────────────────
print(f"Dates filled from PDF fallback ({len(fallback_dates)}):")
for d in fallback_dates:
    print(f"  {d}")
print()

# ── Comparison table ──────────────────────────────────────────────────────────
pdf_dates = sorted(datetime.strptime(d, '%Y-%m-%d') for d in pdf_fallback)
final_dates = sorted(datetime.strptime(d, '%Y-%m-%d') for d in output)
ia_count = sum(1 for v in output.values() if v['source'] == 'ia')
fb_count = sum(1 for v in output.values() if v['source'] == 'pdf_fallback')

def gap_list(dates):
    return [(a, b, (b - a).days - 1)
            for a, b in zip(dates, dates[1:])
            if (b - a).days > 4]

pdf_gaps = gap_list(pdf_dates)
final_gaps = gap_list(final_dates)

print(f"{'':30} {'PDF':>12} {'Final':>12}")
print('─' * 56)
print(f"{'Total entries':<30} {len(pdf_dates):>12} {len(final_dates):>12}")
print(f"{'  IA source':<30} {'':>12} {ia_count:>12}")
print(f"{'  PDF fallback':<30} {'':>12} {fb_count:>12}")
if pdf_dates:
    print(f"{'First date':<30} {pdf_dates[0].strftime('%Y-%m-%d'):>12} {final_dates[0].strftime('%Y-%m-%d'):>12}")
    print(f"{'Last date':<30} {pdf_dates[-1].strftime('%Y-%m-%d'):>12} {final_dates[-1].strftime('%Y-%m-%d'):>12}")
print(f"{'Gaps > 3 days':<30} {len(pdf_gaps):>12} {len(final_gaps):>12}")
for a, b, n in final_gaps:
    print(f"  {a.strftime('%Y-%m-%d')} → {b.strftime('%Y-%m-%d')} ({n} missing)")
