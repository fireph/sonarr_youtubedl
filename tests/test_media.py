import re

import pytest

from sytdl.media import normalize_title, title_pattern


@pytest.mark.parametrize(
    ("expected", "candidate"),
    [
        ("Rock and Roll: John's Cut!", "ROCK & ROLL — Johns Cut"),
        ("A “Quoted” Title", "a quoted title"),
        ("One... Two", "One - Two"),
        ("Full Width 42", "Ｆｕｌｌ Ｗｉｄｔｈ 42"),
    ],
)
def test_title_pattern_matches_normalized_title_variations(expected, candidate):
    assert re.search(title_pattern(expected), normalize_title(candidate))


def test_title_pattern_preserves_word_and_number_boundaries():
    assert not re.search(title_pattern("Episode 42"), normalize_title("Episode 420"))
    assert not re.search(title_pattern("To Get Her"), normalize_title("Together"))


def test_title_pattern_for_punctuation_only_title_never_matches():
    pattern = title_pattern("…?!")

    assert not re.search(pattern, "")
    assert not re.search(pattern, normalize_title("Any title"))
