"""
Print raw OCR text for pages that should cover three gap ranges:
  - 1941-12-21 to 1942-01-02
  - 1942-01-05 to 1942-01-21
  - 1942-05-23 to 1942-06-02
Shows any page where a likely date in those windows appears.
"""
import pdfplumber
import re

PDF_PATH = "1_Inputs/Nimitz_Graybook Volume 1.pdf"

# Month names → number
MONTH_NUMS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

# Loose date scan — any "MonthName DD" anywhere on page
LOOSE_DATE_RE = re.compile(
    r'(January|February|March|April|May|June|July|August'
    r'|September|October|November|December)\s+(\d{1,2})',
    re.IGNORECASE
)

# Gap windows to inspect (inclusive, as (month, day_start, day_end, year))
WINDOWS = [
    {'label': 'Dec 21 1941 – Jan 2 1942',
     'dates': {(12, d, 1941) for d in range(21, 32)} | {(1, d, 1942) for d in range(1, 3)}},
    {'label': 'Jan 5–21 1942',
     'dates': {(1, d, 1942) for d in range(5, 22)}},
    {'label': 'May 23 – Jun 2 1942',
     'dates': {(5, d, 1942) for d in range(23, 32)} | {(6, d, 1942) for d in range(1, 3)}},
]

# Track year roughly: flip Dec→Jan
current_year = 1941
last_month = None

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_num <= 3:
            continue

        raw = page.extract_text() or ''
        hits = LOOSE_DATE_RE.findall(raw)

        for month_str, day_str in hits:
            m = MONTH_NUMS[month_str.lower()]
            d = int(day_str)

            # Year tracking
            if last_month == 12 and m == 1:
                current_year += 1
            last_month = m

            for window in WINDOWS:
                if (m, d, current_year) in window['dates']:
                    print(f"\n{'#'*70}")
                    print(f"  PDF page {page_num}  |  window: {window['label']}")
                    print(f"  Triggered by: {month_str} {day_str} (year={current_year})")
                    print(f"{'#'*70}")
                    print(raw)
                    break  # one report per page per pass
