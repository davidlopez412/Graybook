"""
Conservative text cleaner for graybook_vol1.json.
Only strips trailing garbage lines from each entry — never touches
mid-entry OCR noise. Overwrites the input file in place.
"""
import json
import re

PATH = "3_Outputs/graybook_vol1.json"

# Characters that are scanner artifacts and never appear in real prose
ARTIFACT_RE = re.compile(r'[§~\\|`]')

def alpha_ratio(s):
    return sum(c.isalpha() for c in s) / len(s) if s else 0.0

def is_garbage(line):
    s = line.strip()
    if not s:
        return True
    # Short line containing known scanner artifact characters
    if len(s) <= 30 and ARTIFACT_RE.search(s):
        return True
    # Very short line that is nearly all non-alphabetic
    if len(s) <= 15 and alpha_ratio(s) < 0.35:
        return True
    return False

with open(PATH) as f:
    data = json.load(f)

cleaned = {}
total_removed = 0
entries_touched = 0

for date_key in sorted(data):
    text = data[date_key]
    lines = text.split('\n')
    before = len(lines)

    while lines and is_garbage(lines[-1]):
        lines.pop()

    after = len(lines)
    removed = before - after
    if removed:
        total_removed += removed
        entries_touched += 1

    cleaned[date_key] = '\n'.join(lines).strip()

with open(PATH, 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, indent=2, ensure_ascii=False)

print(f"Entries cleaned  : {entries_touched} of {len(cleaned)}")
print(f"Lines removed    : {total_removed}")
print()

# Show before/after for the four key dates
SPOT_CHECK = ['1941-12-07', '1942-05-25', '1942-06-04', '1942-08-07']
print("Last 2 lines of each spot-check entry after cleaning:")
for key in SPOT_CHECK:
    val = cleaned.get(key, '')
    tail = [l for l in val.split('\n') if l.strip()][-2:]
    print(f"\n  {key}")
    for l in tail:
        print(f"    {l}")
