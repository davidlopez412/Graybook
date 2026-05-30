"""
Raw page dump for the Midway gap (May 23 – Jun 2, 1942).
No section filtering — prints everything pdfplumber extracts from any page
that mentions a date in that window.
"""
import pdfplumber
import re

PDF_PATH = "1_Inputs/Nimitz_Graybook Volume 1.pdf"

# Volume 1 only covers Dec 1941 – Aug 1942, so any May/June date is unambiguously 1942.
# No year tracking needed.
TRIGGER_RE = re.compile(
    r'\b(May\s+(?:2[3-9]|3[01])|June\s+[12])\b',
    re.IGNORECASE
)

printed_pages = set()

with pdfplumber.open(PDF_PATH) as pdf:
    for page_num, page in enumerate(pdf.pages, start=1):
        if page_num <= 3:
            continue

        raw = page.extract_text() or ''
        hit = TRIGGER_RE.search(raw)

        if hit and page_num not in printed_pages:
            printed_pages.add(page_num)
            print(f"\n{'#'*70}")
            print(f"  PDF page {page_num}  |  triggered by: '{hit.group()}'")
            print(f"{'#'*70}")
            print(raw)
