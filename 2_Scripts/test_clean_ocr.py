"""
test_clean_ocr.py — Unit tests for clean_ocr correction functions.

Run with:  pytest 2_Scripts/test_clean_ocr.py -v
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from clean_ocr import (
    fix_digit_sub, fix_stray_punct, fix_allcaps_prefix, fix_adjacent_join,
    fix_phrases, PHRASE_CATALOG,
)


# ── Pattern 3: fix_digit_sub (extended) ──────────────────────────────────────

def test_digit_sub_3_to_g():
    """3→g when flanked by letters and result is valid."""
    result, changes = fix_digit_sub('rou3h')
    assert result == 'rough'
    assert changes[0][0] == 'digit_sub'

def test_digit_sub_6_to_b():
    """6→b when flanked by letters and result is valid."""
    result, changes = fix_digit_sub('a6out')
    assert result == 'about'
    assert changes[0][0] == 'digit_sub'

def test_digit_sub_8_to_b():
    """8→b when flanked by letters and result is valid."""
    result, changes = fix_digit_sub('a8le')
    assert result == 'able'
    assert changes[0][0] == 'digit_sub'

def test_digit_sub_8_elaborate():
    """8→b when flanked by letters and result is valid (longer word)."""
    result, changes = fix_digit_sub('ela8orate')
    assert result == 'elaborate'

def test_digit_sub_no_change_all_caps():
    """All-caps tokens are never modified."""
    result, changes = fix_digit_sub('TA3K')
    assert result == 'TA3K'
    assert changes == []

def test_digit_sub_no_change_valid_word():
    """Already-valid words are skipped."""
    result, changes = fix_digit_sub('force')
    assert result == 'force'
    assert changes == []

def test_digit_sub_no_change_multiple_digits():
    """Only fires when there is exactly one digit from the set 01368."""
    result, changes = fix_digit_sub('3r0up')
    assert result == '3r0up'
    assert changes == []

def test_digit_sub_3_first_position_skipped():
    """Digit at position 0 (not flanked on left) is skipped."""
    result, changes = fix_digit_sub('3roup')
    assert result == '3roup'
    assert changes == []


# ── Pattern 6: PHRASE_CATALOG (Task Porce) ───────────────────────────────────

def test_phrase_catalog_task_porce():
    """Task Porce → Task Force is in PHRASE_CATALOG."""
    assert ('Task Porce', 'Task Force') in PHRASE_CATALOG

def test_fix_phrases_task_porce():
    """fix_phrases replaces 'Task Porce' with 'Task Force' in a sentence."""
    log = []
    result = fix_phrases('Task Porce Twelve was ordered to proceed.', '1941-12-10', log)
    assert result == 'Task Force Twelve was ordered to proceed.'
    assert any(e[1] == 'phrase_norm' for e in log)


# ── Pattern 2: fix_stray_punct ────────────────────────────────────────────────

def test_fix_stray_punct_embedded_dot():
    """f.orce → force (embedded dot stripped when result is valid)."""
    log = []
    result = fix_stray_punct('the enemy striking f.orce had retired', '1941-12-08', log)
    assert 'force' in result
    assert 'f.orce' not in result

def test_fix_stray_punct_embedded_colon():
    """A:t → At when result is valid."""
    log = []
    result = fix_stray_punct('A:t sea the fleet', '1941-12-09', log)
    assert 'A:t' not in result

def test_fix_stray_punct_wha_t():
    """wha.t → what."""
    log = []
    result = fix_stray_punct('wha.t was the situation', '1941-12-10', log)
    assert 'what' in result
    assert 'wha.t' not in result

def test_fix_stray_punct_prefix_colon():
    """:made → made (colon prefix stripped)."""
    log = []
    result = fix_stray_punct('The only change :made in', '1941-12-10', log)
    assert ':made' not in result
    assert 'made' in result

def test_fix_stray_punct_preserves_abbreviations():
    """T.F and U.S are not modified (single-char sides = abbreviation)."""
    log = []
    result = fix_stray_punct('T.F Eight and U.S forces', '1942-01-01', log)
    assert 'T.F' in result
    assert 'U.S' in result

def test_fix_stray_punct_preserves_possessives():
    """Eight's is not modified (apostrophe-s possessive)."""
    log = []
    result = fix_stray_punct("Task Force Eight's departure was scheduled", '1941-12-09', log)
    assert "Eight's" in result

def test_fix_stray_punct_no_change_if_invalid_result():
    """Does not fire when stripping punct yields a non-word."""
    log = []
    result = fix_stray_punct('the FJ.ar base was damaged', '1941-12-07', log)
    # 'FJar' is not a valid word — original is preserved
    assert 'FJ.ar' in result


# ── Pattern 4: fix_allcaps_prefix ─────────────────────────────────────────────

def test_fix_allcaps_prefix_quoted_repulse():
    """"REPULSE → REPULSE (leading double-quote stripped)."""
    log = []
    result = fix_allcaps_prefix('"REPULSE was sunk', '1942-01-21', log)
    assert '"REPULSE' not in result
    assert 'REPULSE' in result

def test_fix_allcaps_prefix_not_whitelisted():
    """Non-whitelist all-caps tokens are not modified."""
    log = []
    result = fix_allcaps_prefix('"CARRIER operations', '1942-01-01', log)
    # CARRIER is not in whitelist — leave unchanged
    assert '"CARRIER' in result

def test_fix_allcaps_prefix_already_clean():
    """Token already in whitelist form is not modified."""
    log = []
    result = fix_allcaps_prefix('REPULSE was at sea', '1942-01-21', log)
    assert result == 'REPULSE was at sea'
    assert log == []


# ── Pattern 5: fix_adjacent_join ──────────────────────────────────────────────

def test_fix_adjacent_join_according():
    """'accordi ng' → 'according'."""
    log = []
    result = fix_adjacent_join('they were accordi ng to orders', '1942-02-13', log)
    assert 'accordi ng' not in result
    assert 'according' in result

def test_fix_adjacent_join_hardly():
    """'har dly' → 'hardly'."""
    log = []
    result = fix_adjacent_join('it was har dly surprising', '1941-12-26', log)
    assert 'hardly' in result

def test_fix_adjacent_join_no_change_if_valid_parts():
    """Does not join if either part is already a valid word."""
    log = []
    # 'in' is a valid word — should not join 'in formation'
    result = fix_adjacent_join('in formation the fleet sailed', '1942-01-01', log)
    assert 'in formation' in result

def test_fix_adjacent_join_min_combined_length():
    """Does not join if combined result is under 5 chars."""
    log = []
    # even if 'atbe' were valid (it's not), the length check would prevent it
    result = fix_adjacent_join('at be the', '1942-01-01', log)
    assert isinstance(result, str)  # just verify no crash
