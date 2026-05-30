import json
import os
import re

# ── Narrative truncation ───────────────────────────────────────────────────────
# Large entries in graybook_vol1.json have absorbed appended documents:
#   • Radio dispatch logs  (day + time + unit: "14 0741 COMNCH...")
#   • Strategic estimates  ("ESTIMATE OF THE SITUATION")
#   • Appendix sections    ("APPENDIX A", "ANNEX", "ENCLOSURE")
#   • Page number stamps   ("-6-")
#   • Continuation headers ("RUNNING SUMMARY OF SITUATION (Cont'd)")
# These patterns mark where the actual daily narrative ends.

_BOUNDARY_PATTERNS = [
    # Structural document markers — trusted at any position
    re.compile(r'^ESTIMATE\s+OF\s+(THE\s+)?SITUATION', re.MULTILINE | re.IGNORECASE),
    re.compile(r'^(APPENDIX|ANNEX|ENCLOSURE)\b',       re.MULTILINE | re.IGNORECASE),
    re.compile(r'^-\s*\d+\s*-\s*$',                    re.MULTILINE),
    re.compile(r'RUNNING\s+S[UW][MN]MARY\s+OF\s+SITUATION.{0,30}Cont', re.IGNORECASE),
]

# Dispatch log markers — only trusted when MIN_NARRATIVE_WORDS of text precede them,
# so entries that open with dispatch traffic (no captured narrative) are left untouched.
_DISPATCH_PATTERNS = [
    re.compile(r'^\d{2}\s+\d{4}\s+[A-Z]{4,}',      re.MULTILINE),  # DD HHMM UNIT
    re.compile(r'^\d{5,6}\s+[A-Z]{3,}\s+TO\s+[A-Z]{3,}', re.MULTILINE),  # DDDHHMM UNIT TO UNIT
]

HARD_CAP_WORDS    = 1000  # absolute ceiling — catches absorbed docs with no clear marker
MIN_DISPATCH_WORDS = 50   # min narrative words before a dispatch marker is trusted

BASE      = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE, '..', '3_Outputs', 'graybook_vol1_clean.json')
OUT_PATH  = os.path.join(BASE, '..', '3_Outputs', 'entries.js')

MONTHS_FULL = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December',
]

def fmt_date(date_str):
    y, m, d = date_str.split('-')
    return f"{int(d)} {MONTHS_FULL[int(m)-1]} {int(y)}"

# Five hand-written historian's notes. All other entries get a placeholder.
HISTORIAN_NOTES = {
    '1941-12-07': {
        'knew': "Admiral Kimmel knew by midday that the battle line had been gutted at its moorings — ARIZONA destroyed, OKLAHOMA capsized, at least four other battleships out of action — and that the enemy had achieved complete tactical surprise. His carrier groups, at sea during the attack, were intact and unharmed.",
        'didntKnow': "He did not yet know that Nagumo had already turned northwest for home, declining a third strike against the fuel farms and repair basins that would have crippled Pearl Harbor for months. He could not know that the carriers' absence from the harbor had been the day's saving grace, nor that phantom contact reports were already driving American search forces in the wrong direction.",
        'coming': "Within three weeks Kimmel would be relieved of command, his career ended by a catastrophe with multiple fathers. Chester Nimitz would arrive on New Year's Eve to raise his flag over a command in ruins — inheriting the lesson this entry only begins to reckon with: that the war would now be carried by the carriers still at sea.",
    },
    '1941-12-31': {
        'knew': "Acting CINCPAC Admiral Pye knew his brief tenure — less than two weeks — had been defined by the loss of Wake Island and the agonizing recall of SARATOGA's relief force within reach of the island. He was handing over to Nimitz a Pacific Fleet stripped of its battle line, with three carriers, a shattered air establishment at Pearl Harbor, and enemy forces pressing on every front.",
        'didntKnow': "He could not know how bitterly the Wake decision would be judged — by the men left on the beach who watched rescue turn away, and by a history weighing one carrier against a garrison already lost. He did not know that the arithmetic he had accepted, cold as it was, would become the foundational logic of Nimitz's entire first year: with only carriers to spend, none could be spent on positions already forfeit.",
        'coming': "Nimitz would spend his first days absorbing the full scope of the disaster before launching cautious carrier raids in February. The calculus Pye had demonstrated — preservation of the carriers above all else — would prove exactly right, and would carry the fleet to Coral Sea and Midway in the months ahead.",
    },
    '1942-05-25': {
        'knew': "Nine days before the Japanese strike force would arrive, Nimitz knew — with a confidence unprecedented in the war — where the enemy was going and when. His codebreakers had broken enough of JN-25 to map Yamamoto's operation in outline: a massive strike on Midway designed to draw out and destroy the American carriers. Three American carriers were sortied or being readied; YORKTOWN, damaged at Coral Sea, was in drydock for emergency repairs.",
        'didntKnow': "He could not be certain his intelligence estimate would hold — whether the Japanese would deviate from plan, whether YORKTOWN would be seaworthy in time, or whether aircrews who had never coordinated a strike of this scale could execute the ambush he had set. If the estimate was wrong, three carriers would be sailing into a trap rather than setting one.",
        'coming': "Ten days hence, four Japanese fleet carriers would be burning within minutes of each other off Midway. The intelligence gamble Nimitz had staked his command on would pay out completely and permanently. It would not end the war, but it would end Japan's freedom to choose where the war was fought.",
    },
    '1942-06-04': {
        'knew': "Forewarned by his codebreakers, Nimitz knew by nightfall that AKAGI, KAGA, SORYU, and HIRYU were burning or sunk. His ambush had worked. The Midway invasion force had turned back without pressing its landing, and YORKTOWN — patched and sent back to sea in seventy-two hours — had done her part before being struck in turn.",
        'didntKnow': "He did not yet grasp the full geometry of what had happened in the minutes that decided the battle — the chance timing that left the Japanese flight decks crowded with armed and fueled aircraft when the dive-bombers arrived. He could not yet measure what it meant that four carriers and the veteran aircrews who had executed Pearl Harbor, Coral Sea, and the Indian Ocean raids were gone irreversibly.",
        'coming': "Midway ended Japan's strategic initiative. The next offensive move would be American — and it was already being planned for Guadalcanal and the Solomons. The six months ahead would be savage and nearly lost, but they would be fought on terms Japan had not chosen and could not sustain.",
    },
    '1942-08-07': {
        'knew': "Nimitz knew the First Marine Division had landed on Guadalcanal and Tulagi and seized the nearly-complete Japanese airfield intact. Shore resistance had been lighter than feared; air reaction from Rabaul was heavy but had not stopped the operation. The airfield — the entire strategic rationale for WATCHTOWER — was in American hands on the first day.",
        'didntKnow': "He did not yet know that the easy landing was the last easy thing about Guadalcanal. He could not anticipate how quickly and violently the Japanese Navy would answer — within forty-eight hours Mikawa's cruiser column would shatter the Allied screening force off Savo Island and send four heavy cruisers to the bottom. He did not know the campaign would consume both navies through the end of 1942.",
        'coming': "The Marines ashore would spend the next six months fighting to hold the perimeter around Henderson Field while the Navy contested the supply routes in a series of brutal night engagements. What planners had called WATCHTOWER — suggesting a cautious, defensive beginning — would become the longest and most contested campaign of the American naval war.",
    },
}


def get_note(date_str):
    if date_str in HISTORIAN_NOTES:
        return HISTORIAN_NOTES[date_str]
    return {
        'knew': f"Historian's Note coming soon. This entry covers {fmt_date(date_str)}. The full AI interpretation feature will be enabled in a future version.",
        'didntKnow': '',
        'coming': '',
    }


def truncate_to_narrative(text):
    """
    Return only the portion of text that is genuine running summary prose,
    stripping absorbed dispatch logs and planning documents.
    Entries at or under HARD_CAP_WORDS are returned unchanged.
    """
    if len(text.split()) <= HARD_CAP_WORDS:
        return text

    # 1. Structural markers — highest confidence, truncate immediately on match.
    for pat in _BOUNDARY_PATTERNS:
        m = pat.search(text)
        if m and m.start() > 0:
            candidate = text[:m.start()].rstrip()
            if candidate:
                words = candidate.split()
                return ' '.join(words[:HARD_CAP_WORDS]) if len(words) > HARD_CAP_WORDS else candidate

    # 2. Dispatch log markers — only when enough narrative precedes them,
    #    so entries that open entirely with dispatch traffic are left untouched.
    for pat in _DISPATCH_PATTERNS:
        m = pat.search(text)
        if m:
            prefix_words = len(text[:m.start()].split())
            if prefix_words >= MIN_DISPATCH_WORDS:
                candidate = text[:m.start()].rstrip()
                if candidate:
                    words = candidate.split()
                    return ' '.join(words[:HARD_CAP_WORDS]) if len(words) > HARD_CAP_WORDS else candidate

    # 3. No clear boundary — apply hard cap.
    return ' '.join(text.split()[:HARD_CAP_WORDS])


def get_command(date_str):
    if date_str <= '1941-12-30':
        return 'ADM. H. E. KIMMEL, CINCPAC'
    elif date_str == '1941-12-31':
        return 'VICE ADM. W. S. PYE, ACTING CINCPAC'
    return 'ADM. C. W. NIMITZ, CINCPAC'


def extract_event(text):
    for line in text.split('\n'):
        line = line.strip()
        if len(line) < 4:
            continue
        if line[0].isalpha() and sum(c.isalpha() for c in line) / len(line) >= 0.60:
            return line[:60]
    return ''


# Characters that are clearly non-standard in a WWII document corpus.
# Matches anything that is not: letter, digit, whitespace, or common punctuation.
_SYMBOL_RE = re.compile(r"[^a-zA-Z0-9\s.,\-'\"/:;!?()—–’‘“”&]")


def has_ocr_garbage(text):
    if len(_SYMBOL_RE.findall(text)) > 2:
        return True
    if '~' in text:
        return True
    # Word starting lowercase then immediately uppercase: "lJapanese" (not "MacArthur",
    # where the uppercase is mid-word, not at a word boundary).
    if re.search(r'\b[a-z][A-Z]', text):
        return True
    # TWO_UPPERCASE then lowercase with or without separator: "FJ.ar", "FJarb"
    if re.search(r'[A-Z]{2}\.?[a-z]', text):
        return True
    return False


def is_continuation(chunk):
    """True if this chunk should be merged onto the previous paragraph."""
    if not chunk:
        return False
    if chunk[0].islower() or chunk[0] == ',':
        return True
    if len(chunk.split()) < 8:
        return True
    return False


def merge_fragments(paras):
    """Merge paragraph chunks that are clearly continuations of the previous."""
    if not paras:
        return paras
    merged = [paras[0]]
    for chunk in paras[1:]:
        prev_incomplete = not re.search(r'[.?!]\s*$', merged[-1])
        if prev_incomplete or is_continuation(chunk):
            merged[-1] = merged[-1] + ' ' + chunk
        else:
            merged.append(chunk)
    return merged


def split_actual(text):
    paras = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paras) <= 1:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return [{'text': text.strip(), 'degraded': False}]
        paras = [' '.join(lines[i:i + 3]) for i in range(0, len(lines), 3)]
    paras = merge_fragments(paras)
    return [{'text': p, 'degraded': has_ocr_garbage(p)} for p in paras]


def build_entry(date, text):
    narrative = truncate_to_narrative(text)
    return {
        'date':    date,
        'event':   extract_event(text),      # use full text — event label is always first line
        'place':   '',
        'command': get_command(date),
        'actual':  split_actual(narrative),  # display only the narrative portion
        'note':    get_note(date),
    }


def main():
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)

    dates   = sorted(data.keys())
    entries = [build_entry(d, data[d]) for d in dates]

    degraded_count = sum(
        1 for e in entries for p in e['actual'] if p['degraded']
    )
    truncated = [(d, len(data[d].split()), sum(len(p['text'].split()) for p in build_entry(d, data[d])['actual']))
                 for d in dates if len(data[d].split()) > HARD_CAP_WORDS]
    truncated = [(d, orig, kept) for d, orig, kept in truncated if orig != kept]

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(f'window.WAR_TIMELINE = {{ start: "{dates[0]}", end: "{dates[-1]}" }};\n\n')
        f.write('window.ENTRIES = ')
        f.write(json.dumps(entries, indent=2, ensure_ascii=False))
        f.write(';\n')

    noted = sum(1 for e in entries if e['date'] in HISTORIAN_NOTES)
    print(f'Wrote {len(entries)} entries ({noted} with full historian notes, '
          f'{degraded_count} degraded paragraphs) → {OUT_PATH}')
    if truncated:
        print(f'Truncated {len(truncated)} entries (original → kept words):')
        for d, orig, kept in sorted(truncated, key=lambda x: -x[1]):
            print(f'  {d}: {orig} → {kept}')


if __name__ == '__main__':
    main()
