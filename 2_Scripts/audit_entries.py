import json
import os
import re
from collections import namedtuple

BASE       = os.path.dirname(os.path.abspath(__file__))
JSON_PATH  = os.path.join(BASE, '..', '3_Outputs', 'graybook_vol1.json')
JS_PATH    = os.path.join(BASE, '..', '3_Outputs', 'entries.js')
OUT_PATH   = os.path.join(BASE, '..', 'docs', 'entry_audit.txt')


def load_entries_js():
    """Parse entries.js and return {date: displayed_text} using the actual[] paragraphs."""
    src = open(JS_PATH, encoding='utf-8').read()
    m = re.search(r'window\.ENTRIES\s*=\s*(\[.*\]);', src, re.DOTALL)
    entries = json.loads(m.group(1))
    return {
        e['date']: '\n\n'.join(p['text'] for p in e['actual'])
        for e in entries
    }


def load_raw_json():
    """Return {date: raw_ocr_text} from the source JSON."""
    data = json.load(open(JSON_PATH, encoding='utf-8'))
    return {d: v['text'] for d, v in data.items()}

# Thresholds
OCR_FLAG_THRESHOLD = 5    # noise score above this → OCR flag
MIN_WORD_COUNT     = 100  # below this word count → length flag
SHORT_PARA_RATIO   = 0.30 # fraction of <10-word paragraphs → coherence flag

EntryResult = namedtuple(
    'EntryResult',
    ['date', 'word_count', 'ocr_score', 'short_para_ratio', 'flags']
)


def ocr_noise_score(text):
    score = 0

    # 1. Non-standard characters embedded between alphanumeric chars.
    # Targets OCR artifacts like tildes, pipes, backslashes, brackets, etc.
    # Standard punctuation (.,;:!?-'"()) excluded — those appear in clean text.
    embedded = re.findall(r'[a-zA-Z0-9][~|\\@#$%^*\[\]{}<>=+`][a-zA-Z0-9]', text)
    score += len(embedded)

    # 2. Digit 0 or 1 sandwiched between letters — classic single-char substitution
    # (OCR reads lowercase L as 1, uppercase O as 0).
    substitutions = re.findall(r'[a-zA-Z][01][a-zA-Z]', text)
    score += len(substitutions)

    # 3. Alphanumeric runs longer than 4 chars where fewer than half the chars are
    # alphabetic — indicates garbled tokens like "1~lJD" or "0f75x".
    for tok in re.findall(r'[a-zA-Z0-9]{5,}', text):
        if sum(c.isalpha() for c in tok) / len(tok) < 0.5:
            score += 1

    return score


def get_paragraphs(text):
    """Split entry text into paragraphs, falling back to line-by-line if needed."""
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paras) <= 1:
        paras = [ln.strip() for ln in text.split('\n') if ln.strip()]
    return paras


def audit_entry(date, text):
    flags = []

    # --- OCR noise ---
    ocr = ocr_noise_score(text)
    if ocr > OCR_FLAG_THRESHOLD:
        flags.append(f'ocr_score={ocr}')

    # --- Length ---
    words = len(text.split())
    if words < MIN_WORD_COUNT:
        flags.append(f'too_short={words}w')

    # --- Paragraph coherence ---
    paras = get_paragraphs(text)
    short_paras = [p for p in paras if len(p.split()) < 10]
    ratio = len(short_paras) / len(paras) if paras else 0.0
    if ratio > SHORT_PARA_RATIO:
        flags.append(f'frag_paras={len(short_paras)}/{len(paras)}={ratio:.0%}')

    return EntryResult(
        date=date,
        word_count=words,
        ocr_score=ocr,
        short_para_ratio=ratio,
        flags=flags,
    )


def fmt_entry(r):
    flags_str = ', '.join(r.flags) if r.flags else '—'
    return (
        f"  {r.date}  "
        f"words:{r.word_count:>4}  "
        f"ocr:{r.ocr_score:>3}  "
        f"frags:{r.short_para_ratio:>4.0%}  "
        f"[{flags_str}]"
    )


def classify(results):
    clean = [r for r in results if len(r.flags) == 0]
    minor = [r for r in results if len(r.flags) in (1, 2)]
    major = [r for r in results if len(r.flags) >= 3]
    return clean, minor, major


def avg_words(results):
    return sum(r.word_count for r in results) / len(results) if results else 0


def main():
    raw  = load_raw_json()
    disp = load_entries_js()

    before = [audit_entry(d, t) for d, t in sorted(raw.items())]
    after  = [audit_entry(d, t) for d, t in sorted(disp.items())]

    bc, bm, bx = classify(before)
    ac, am, ax = classify(after)

    W = 72
    lines = []

    lines.append('ENTRY AUDIT — Nimitz Graybook Vol. I')
    lines.append('=' * W)
    lines.append(f'{"":30}  {"BEFORE":>10}  {"AFTER (displayed)":>17}')
    lines.append(f'{"":30}  {"(raw JSON)":>10}  {"(entries.js)":>17}')
    lines.append('-' * W)
    n = len(before)
    lines.append(f'{"Clean (0 flags)":30}  {len(bc):>5} ({len(bc)/n:.0%})  {len(ac):>8} ({len(ac)/n:.0%})')
    lines.append(f'{"Minor issues (1–2 flags)":30}  {len(bm):>5} ({len(bm)/n:.0%})  {len(am):>8} ({len(am)/n:.0%})')
    lines.append(f'{"Significant (3+ flags)":30}  {len(bx):>5} ({len(bx)/n:.0%})  {len(ax):>8} ({len(ax)/n:.0%})')
    lines.append('-' * W)
    lines.append(f'{"Avg words / entry":30}  {avg_words(before):>10.0f}  {avg_words(after):>17.0f}')
    lines.append(f'{"Median words / entry":30}  {sorted(r.word_count for r in before)[n//2]:>10}  '
                 f'{sorted(r.word_count for r in after)[n//2]:>17}')
    lines.append(f'{"Max words / entry":30}  {max(r.word_count for r in before):>10}  '
                 f'{max(r.word_count for r in after):>17}')
    lines.append('')
    lines.append(f'Thresholds: OCR > {OCR_FLAG_THRESHOLD}  |  short < {MIN_WORD_COUNT}w  |  '
                 f'frags > {SHORT_PARA_RATIO:.0%} paras under 10 words')
    lines.append('Columns: date  words  ocr  frags  [flags]')
    lines.append('')

    sections = [
        ('CLEAN',              ac, 'no flags — display-ready'),
        ('MINOR ISSUES',       am, '1–2 flags — readable but imperfect'),
        ('SIGNIFICANT ISSUES', ax, '3+ flags — needs attention'),
    ]
    for label, group, note in sections:
        lines.append(f'{label}  ({len(group)} entries — {note})')
        lines.append('-' * W)
        for r in group:
            lines.append(fmt_entry(r))
        if not group:
            lines.append('  (none)')
        lines.append('')

    output = '\n'.join(lines)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    open(OUT_PATH, 'w', encoding='utf-8').write(output)

    # Stdout: comparison table only
    for line in lines[:14]:
        print(line)
    print(f'\nFull report → {OUT_PATH}')


if __name__ == '__main__':
    main()
