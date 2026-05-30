import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from build_entries import (
    get_command, extract_event, split_actual,
    is_continuation, merge_fragments, has_ocr_garbage,
)


# --- get_command ---

def test_command_kimmel_first_day():
    assert get_command('1941-12-07') == 'ADM. H. E. KIMMEL, CINCPAC'

def test_command_kimmel_last_day():
    assert get_command('1941-12-30') == 'ADM. H. E. KIMMEL, CINCPAC'

def test_command_pye():
    assert get_command('1941-12-31') == 'VICE ADM. W. S. PYE, ACTING CINCPAC'

def test_command_nimitz_first_day():
    assert get_command('1942-01-01') == 'ADM. C. W. NIMITZ, CINCPAC'

def test_command_nimitz_late():
    assert get_command('1942-09-03') == 'ADM. C. W. NIMITZ, CINCPAC'


# --- extract_event ---

def test_extract_event_clean_first_line():
    text = 'Task Force Eight sorties from Pearl Harbor.\nMore text here.'
    assert extract_event(text) == 'Task Force Eight sorties from Pearl Harbor.'

def test_extract_event_skips_ocr_garbage_first_line():
    text = '1~1hen :~x garbage\nTask Force Eight sorties from Pearl Harbor.'
    assert extract_event(text) == 'Task Force Eight sorties from Pearl Harbor.'

def test_extract_event_skips_very_short_lines():
    text = 'OK\nTask Force Eight sorties from Pearl Harbor.'
    assert extract_event(text) == 'Task Force Eight sorties from Pearl Harbor.'

def test_extract_event_all_garbage_returns_empty():
    text = '1~1\n:~x\n!!!'
    assert extract_event(text) == ''

def test_extract_event_truncates_to_60():
    text = 'A' * 70
    result = extract_event(text)
    assert result == 'A' * 60

def test_extract_event_empty_string():
    assert extract_event('') == ''


# --- is_continuation ---

def test_is_continuation_lowercase_start():
    assert is_continuation('continued from the previous sentence.')

def test_is_continuation_comma_start():
    assert is_continuation(', and further details follow.')

def test_is_continuation_short_chunk():
    assert is_continuation('Only six words here now.')  # 6 words < 8

def test_is_continuation_long_proper_start():
    assert not is_continuation('Task Force Eight sorties from Pearl Harbor at dawn.')

def test_is_continuation_empty():
    assert not is_continuation('')


# --- merge_fragments ---

def test_merge_fragments_merges_lowercase_continuation():
    paras = ['First sentence ends here.', 'continuing from the first.']
    result = merge_fragments(paras)
    assert len(result) == 1
    assert 'continuing' in result[0]

def test_merge_fragments_merges_when_prev_has_no_terminal_punct():
    # Previous chunk ends mid-sentence (no . ? !) → merge regardless of next chunk's start
    paras = ['The fleet was ordered to engage the enemy at', 'dawn on the following morning.']
    result = merge_fragments(paras)
    assert len(result) == 1
    assert 'dawn' in result[0]

def test_merge_fragments_keeps_proper_start():
    paras = ['First paragraph ends with a period.', 'Second paragraph starts properly with a full sentence.']
    result = merge_fragments(paras)
    assert len(result) == 2

def test_merge_fragments_merges_short_chunk():
    paras = ['First paragraph is long enough to stand alone.', 'Short bit.']  # 2 words
    result = merge_fragments(paras)
    assert len(result) == 1

def test_merge_fragments_never_merges_first():
    paras = ['Only five words here.']  # short, but first — never merged
    result = merge_fragments(paras)
    assert len(result) == 1


# --- has_ocr_garbage ---

def test_has_ocr_garbage_tilde():
    assert has_ocr_garbage('1~1hen the first attack')

def test_has_ocr_garbage_symbol_count():
    assert has_ocr_garbage('text with |many| ~strange~ symbols')

def test_has_ocr_garbage_word_starts_lowercase_then_upper():
    # lJapanese: word boundary + lowercase + uppercase = OCR confusion
    assert has_ocr_garbage('The lJapanese forces attacked at dawn.')

def test_has_ocr_garbage_two_upper_no_period():
    # FJarb = two uppercase immediately followed by lowercase (no separator needed)
    assert has_ocr_garbage('Pearl FJarb or the harbor')

def test_has_ocr_garbage_proper_noun_ok():
    # MacArthur: uppercase is mid-word, not at a word boundary — should not flag
    assert not has_ocr_garbage('MacArthur commanded forces in the Philippines.')

def test_has_ocr_garbage_two_upper_period_lower():
    assert has_ocr_garbage('Pearl FJ.ar or the harbor')

def test_has_ocr_garbage_clean_text():
    assert not has_ocr_garbage('Task Force Eight sorties from Pearl Harbor at dawn.')

def test_has_ocr_garbage_normal_punctuation_ok():
    assert not has_ocr_garbage("Enemy carriers' position unknown; search continues.")


# --- split_actual (returns list of {text, degraded} dicts) ---

def test_split_actual_double_newline():
    # Each paragraph must be >= 8 words to avoid the fragment-merger
    p1 = 'The fleet sortied to engage the enemy carrier force at dawn.'
    p2 = 'Carrier aircraft struck Japanese installations on the Marshall Islands.'
    p3 = 'Task forces retired at high speed to the northeast.'
    text = p1 + '\n\n' + p2 + '\n\n' + p3
    result = split_actual(text)
    assert len(result) == 3
    assert result[0]['text'] == p1
    assert result[1]['text'] == p2
    assert result[2]['text'] == p3

def test_split_actual_single_newline_fallback_groups_lines():
    # Each 3-line chunk must be >= 8 words total to avoid the fragment-merger
    line = 'Task Force Eight was deployed to the western Pacific theater.'
    text = '\n'.join([line] * 6)
    result = split_actual(text)
    assert len(result) == 2
    assert line in result[0]['text']
    assert line in result[1]['text']

def test_split_actual_empty_string():
    result = split_actual('')
    assert result == [{'text': '', 'degraded': False}]

def test_split_actual_degraded_flag():
    text = 'Clean opening paragraph.\n\n1~1hen this line has OCR garbage in it.'
    result = split_actual(text)
    assert result[0]['degraded'] is False
    assert result[1]['degraded'] is True

def test_split_actual_merges_continuation_before_degraded_check():
    # A lowercase continuation should be merged; result should be one paragraph
    text = 'Proper opening sentence that is long enough.\n\ncontinuing mid-sentence here.'
    result = split_actual(text)
    assert len(result) == 1
    assert 'continuing' in result[0]['text']
