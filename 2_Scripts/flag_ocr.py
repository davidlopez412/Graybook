"""
flag_ocr.py — Scan graybook_vol1.json and report suspicious tokens by category.

Usage:
    python3 2_Scripts/flag_ocr.py
    python3 2_Scripts/flag_ocr.py path/to/other.json
"""
import json, re, sys, os
from collections import defaultdict, Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from clean_ocr import valid  # reuse existing dict + valid()

BASE     = Path(__file__).parent
JSON_IN  = BASE / '..' / '3_Outputs' / 'graybook_vol1.json'


def flag_entry(date, text):
    """Return dict of category → list of token strings for this entry."""
    flags = defaultdict(list)
    words = text.split()

    # mixed_punct: alpha(2+).alpha(2+) where stripping punct yields a valid word
    for m in re.finditer(r'([a-zA-Z]{2,})[.;:]([a-zA-Z]{2,})', text):
        left, right = m.group(1), m.group(2)
        combined = left + right
        if valid(combined.lower()) and not valid(left.lower()) and not valid(right.lower()):
            flags['mixed_punct'].append(m.group(0))

    # abbrev_prefix: non-alpha noise before 4+ char all-caps run
    for m in re.finditer(r'[^A-Za-z0-9\s]([A-Z]{4,})', text):
        flags['abbrev_prefix'].append(m.group(0))

    # digit_mix: token with 3/6/8 flanked by at least one alpha on each side
    for m in re.finditer(r'[a-zA-Z][a-zA-Z0-9]*[368][a-zA-Z][a-zA-Z0-9]*|[a-zA-Z][a-zA-Z0-9]*[a-zA-Z][368][a-zA-Z0-9]*', text):
        flags['digit_mix'].append(m.group(0))

    # adjacent_split: two pure-alpha tokens (2-8 chars) both invalid, combined valid 5+
    for i in range(len(words) - 1):
        w1 = re.sub(r'[^a-zA-Z]', '', words[i])
        w2 = re.sub(r'[^a-zA-Z]', '', words[i+1])
        if (2 <= len(w1) <= 8 and 2 <= len(w2) <= 8 and
                not valid(w1.lower()) and not valid(w2.lower())):
            combined = w1 + w2
            if len(combined) >= 5 and valid(combined.lower()):
                flags['adjacent_split'].append(f'{w1}+{w2}')

    return flags


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else JSON_IN
    data = json.loads(path.read_text(encoding='utf-8'))
    dates = sorted(data.keys())

    totals  = defaultdict(Counter)   # category → Counter of token

    for date in dates:
        flags = flag_entry(date, data[date]['text'])
        for cat, tokens in flags.items():
            for t in tokens:
                totals[cat][t] += 1

    print(f'FLAG REPORT — {path.name}  ({len(dates)} entries)')
    print('=' * 63)
    header = f'{"CATEGORY":<18} {"COUNT":>6}  SAMPLE TOKENS'
    print(header)
    print('-' * 63)

    category_order = ['mixed_punct', 'digit_mix', 'adjacent_split', 'abbrev_prefix']
    for cat in category_order:
        if cat not in totals:
            continue
        cnt = sum(totals[cat].values())
        samples = ', '.join(t for t, _ in totals[cat].most_common(8))
        if len(samples) > 55:
            samples = samples[:52] + '...'
        print(f'{cat:<18} {cnt:>6}  {samples}')

    print()
    print('Top 20 mixed_punct tokens by frequency:')
    for token, n in totals['mixed_punct'].most_common(20):
        print(f'  {n:>4}x  {token!r}')

    print()
    print('Top 20 digit_mix tokens by frequency:')
    for token, n in totals['digit_mix'].most_common(20):
        print(f'  {n:>4}x  {token!r}')


if __name__ == '__main__':
    main()
