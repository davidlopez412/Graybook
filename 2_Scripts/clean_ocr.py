"""
clean_ocr.py — Conservative OCR correction for graybook_vol1.json.

Rules applied (in pipeline order per word):
  1. Strip stray ~ and \\ embedded between alphanumeric chars
  2. Remove spurious leading lowercase-l before a capital letter (lJapanese → Japanese)
  3. Replace a single digit 1/0 with l/I/O when flanked by letters and the result
     is a valid English word but the original is not
  4. Replace 'rn' with 'm' when the result is a valid word and the original is not
  5. Swap adjacent characters when exactly one swap produces a valid word
     (unambiguous transpositions only; minimum 7-char words)
  6. Join words split across lines by a hyphen (rein-\nforcements → reinforcements)

Invariants:
  - All-caps tokens (CINCPAC, USS, etc.) are never modified
  - Dictionary checks are case-insensitive
  - Corrections requiring valid() guard are skipped if the original is already valid
"""
import json
import os
import re
from pathlib import Path
from collections import Counter

BASE     = Path(__file__).parent
JSON_IN  = BASE / '..' / '3_Outputs' / 'graybook_vol1.json'
JSON_OUT = BASE / '..' / '3_Outputs' / 'graybook_vol1_clean.json'
LOG_PATH = BASE / '..' / 'docs' / 'ocr_corrections.log'

# ── Dictionary ─────────────────────────────────────────────────────────────────

def _load_words():
    for path in ('/usr/share/dict/words', '/usr/share/dict/american-english'):
        if os.path.exists(path):
            return {w.strip().lower() for w in open(path, encoding='latin-1')}
    return set()

WORDS = _load_words()

# The macOS /usr/share/dict/words omits most inflected forms (plurals, past tenses,
# etc.). Strip common suffixes before the dictionary lookup so that "boats", "forces",
# "arrived", "replied" all register as valid and are never modified by the guards.
_SUFFIX_RULES = [
    ('ying',  ['y']),           # replying → reply
    ('ied',   ['y']),           # replied → reply, complied → comply
    ('ing',   ['', 'e']),       # proceeding → proceed, using → use
    ('red',   ['r']),           # conferred → confer, occurred → occur
    ('ed',    ['', 'e']),       # arrived → arrive
    ('est',   ['', 'e']),       # closest → close, fastest → fast
    ('ers',   ['', 'e']),       # destroyers → destroy
    ('es',    ['', 'e']),       # forces → force
    ('s',     ['']),            # boats → boat, ships → ship
    ('er',    ['', 'e']),       # carrier → carry (less reliable, last)
    ('ly',    ['']),            # rapidly → rapid
    ('tion',  ['te', '']),      # operation → operate
]

def valid(s):
    if not s:
        return False
    t = s.lower()
    if not t.isalpha():
        return False
    if t in WORDS:
        return True
    for suffix, stems in _SUFFIX_RULES:
        if t.endswith(suffix) and len(t) > len(suffix) + 2:
            base = t[:-len(suffix)]
            for alt in stems:
                if (base + alt) in WORDS:
                    return True
    return False

def all_caps(s):
    return s.isalpha() and s == s.upper() and len(s) > 1

# ── Phrase normalization ──────────────────────────────────────────────────────
# Pre-pass applied before word tokenisation. Handles garbled sequences that
# span word boundaries or contain characters the word-level pipeline can't reach.
# Pairs are matched as plain strings in the order listed; put longer/more-specific
# variants before shorter ones that share a prefix.

PHRASE_CATALOG = [
    # RUNNING SUMMARY header variants
    ('RUNNING SUMI\\JARY OF SITUATION',    'RUNNING SUMMARY OF SITUATION'),
    ('RUNNING SUMIYIARY OF SITUATION',     'RUNNING SUMMARY OF SITUATION'),
    ('RUNNING SUW~ARY OF SITUATION',       'RUNNING SUMMARY OF SITUATION'),
    ('RUNNING Sill~IARY OF SITUATION',     'RUNNING SUMMARY OF SITUATION'),
    ('RUNNING SID~MARY OF SITUATION',      'RUNNING SUMMARY OF SITUATION'),
    ('RUNNING SIDKMARY OF SITUATION',      'RUNNING SUMMARY OF SITUATION'),
    ('RUNNING SUiviWili.RY OF SITUATION',  'RUNNING SUMMARY OF SITUATION'),
    # SUMMARY standalone variants
    ('SUMI\\JARY',  'SUMMARY'),
    ('SUMIYIARY',   'SUMMARY'),
    ('Sum~arv',     'Summary'),
    ('Sumr1ary',    'Summary'),
    ('sumnary',     'summary'),
    # COMINCH — more specific before less specific
    ('CoMinch',     'COMINCH'),
    ('coMINCH',     'COMINCH'),
    ('Comineh',     'COMINCH'),
    ('Cominch',     'COMINCH'),
    # CINCPAC garbles
    ("CINCF'AC",    'CINCPAC'),
    ('CINCFAC',     'CINCPAC'),
    ('CINC~AC',     'CINCPAC'),
    ('CINCPAO',     'CINCPAC'),
    ('CINCPAG',     'CINCPAC'),
    ('CINCPJC',     'CINCPAC'),
]


def fix_phrases(text, date, log):
    """Verbatim replacement of known garbled phrases, logged per occurrence."""
    for garbled, correct in PHRASE_CATALOG:
        if garbled in text:
            for _ in range(text.count(garbled)):
                log.append((date, 'phrase_norm', garbled, correct))
            text = text.replace(garbled, correct)
    return text


# ── Word-level corrections ─────────────────────────────────────────────────────

def fix_stray_symbols(word):
    """Remove ~ and \\ embedded between alphanumeric chars.
    If stripping leaves an invalid word, try inserting each letter of the
    alphabet at the gap position and accept the first valid result (symbol_repair)."""
    if all_caps(word):
        return word, []

    # Find the first embedded symbol and its position in the original word
    m = re.search(r'(?<=[a-zA-Z0-9])[~\\](?=[a-zA-Z0-9])', word)
    if not m:
        return word, []

    cleaned = re.sub(r'(?<=[a-zA-Z0-9])[~\\](?=[a-zA-Z0-9])', '', word)

    if valid(cleaned):
        return cleaned, [('stray_symbol', word, cleaned)]

    # Stripped result is not a valid word — try inserting a letter at the gap
    gap = m.start()  # position in original; after stripping, gap shrinks by 1
    insert_pos = gap  # position in cleaned string where the symbol was
    for letter in 'aeioulnrstbcdfghjkmpqvwxyz':  # vowels first — more likely
        candidate = cleaned[:insert_pos] + letter + cleaned[insert_pos:]
        if valid(candidate):
            return candidate, [('symbol_repair', word, candidate)]

    # Neither stripping nor insertion worked — return stripped form anyway
    return cleaned, [('stray_symbol', word, cleaned)]


def fix_leading_l(word):
    """lJapanese → Japanese: lowercase-l before an uppercase letter.
    Only fires when the result is a valid word and not all-caps (ruling out
    lVALES → VALES type false positives where the l was part of an abbreviation)."""
    if len(word) >= 3 and word[0] == 'l' and word[1].isupper():
        candidate = word[1:]
        if not all_caps(candidate) and valid(candidate):
            return candidate, [('leading_l', word, candidate)]
    return word, []


def fix_digit_sub(word):
    """Single-digit substitution: 1→l/I, 0→O, 3→g, 6→b, 8→b/B, flanked by letters."""
    if all_caps(word) or valid(word):
        return word, []
    digits = [(i, ch) for i, ch in enumerate(word) if ch in '01368']
    if len(digits) != 1:
        return word, []
    i, ch = digits[0]
    if i == 0 or i == len(word) - 1:
        return word, []
    if not (word[i - 1].isalpha() and word[i + 1].isalpha()):
        return word, []
    replacements = {
        '1': ['l', 'I'],
        '0': ['O'],
        '3': ['g'],
        '6': ['b'],
        '8': ['b', 'B'],
    }
    for rep in replacements[ch]:
        candidate = word[:i] + rep + word[i + 1:]
        if valid(candidate):
            return candidate, [('digit_sub', word, candidate)]
    return word, []


def fix_rn_to_m(word):
    """rn → m when the result is a valid word and the original is not."""
    if all_caps(word) or valid(word) or 'rn' not in word:
        return word, []
    candidate = word.replace('rn', 'm', 1)   # replace first occurrence only
    if valid(candidate):
        return candidate, [('rn_m', word, candidate)]
    return word, []


def fix_transposition(word):
    """Swap adjacent chars; apply only when exactly one swap yields a valid word.
    Disabled in the default pipeline — adjacent-swap transpositions are rare in OCR
    compared to substitutions, and the false-positive rate on inflected forms and
    OCR fragments is too high for conservative correction. Kept here for reference."""
    if all_caps(word) or valid(word) or len(word) < 7:
        return word, []
    candidates = []
    for i in range(len(word) - 1):
        if word[i] == word[i + 1]:
            continue
        swapped = word[:i] + word[i + 1] + word[i] + word[i + 2:]
        if valid(swapped):
            candidates.append(swapped)
    if len(candidates) == 1:
        return candidates[0], [('transposition', word, candidates[0])]
    return word, []


PIPELINE = [fix_stray_symbols, fix_leading_l, fix_digit_sub, fix_rn_to_m]


def correct_word(word, date, log):
    for fn in PIPELINE:
        word, changes = fn(word)
        for entry in changes:
            log.append((date,) + entry)   # (date, rule, original, corrected)
    return word


# ── Text-level: hyphenated line breaks ────────────────────────────────────────

def fix_hyphen_breaks(text, date, log):
    """Join end-of-line hyphens when the combined word is valid."""
    def try_join(m):
        first, second = m.group(1), m.group(2)
        if all_caps(first) or all_caps(second):
            return m.group(0)
        joined = first + second
        if valid(joined.lower()):
            log.append((date, 'hyphen_join', f'{first}-{second}', joined))
            return joined
        return m.group(0)
    return re.sub(r'([a-zA-Z]{2,})-[ \t]*\n[ \t]*([a-zA-Z]{2,})', try_join, text)


# ── Token regex — matches word-like sequences that may contain OCR artifacts ──

WORD_RE = re.compile(r'[a-zA-Z][a-zA-Z0-9~\\]*')


def correct_text(date, text, log):
    # Pass 0: phrase-level normalization (before word tokenisation)
    text = fix_phrases(text, date, log)
    # Pass 1: multi-token hyphen joining (must run on full text)
    text = fix_hyphen_breaks(text, date, log)
    # Pass 2: per-word corrections
    return WORD_RE.sub(lambda m: correct_word(m.group(0), date, log), text)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if not WORDS:
        print('ERROR: no word list found — install /usr/share/dict/words')
        return

    data = json.loads(JSON_IN.read_text(encoding='utf-8'))
    corrected = {}
    log = []  # (date, rule, original, corrected)

    for date in sorted(data):
        entry = data[date]
        corrected[date] = {
            'text': correct_text(date, entry['text'], log),
            'page': entry['page'],
        }

    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(
        json.dumps(corrected, indent=2, ensure_ascii=False), encoding='utf-8'
    )

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, 'w', encoding='utf-8') as f:
        f.write(f'OCR Corrections — {len(log)} substitutions across {len(data)} entries\n')
        f.write('=' * 72 + '\n')
        f.write(f'{"DATE":<12} {"RULE":<16} {"ORIGINAL":<28} CORRECTED\n')
        f.write('-' * 72 + '\n')
        for date, rule, orig, corr in log:
            f.write(f'{date:<12} {rule:<16} {orig:<28} {corr}\n')

    rule_counts = Counter(rule for _, rule, _, _ in log)

    print(f'Total substitutions : {len(log):,}')
    print(f'Entries modified    : {len({d for d,_,_,_ in log})} of {len(data)}')
    print()
    print('By rule:')
    for rule, n in rule_counts.most_common():
        print(f'  {rule:<18} {n:>6}')
    print()
    print('Sample of 20 corrections:')
    seen = set()
    shown = 0
    for date, rule, orig, corr in log:
        key = (rule, orig, corr)
        if key in seen:
            continue
        seen.add(key)
        print(f'  {date}  [{rule:<16}]  {orig!r:>28} → {corr!r}')
        shown += 1
        if shown == 20:
            break
    print()
    print(f'Output → {JSON_OUT}')
    print(f'Log    → {LOG_PATH}')


if __name__ == '__main__':
    main()
