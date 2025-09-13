import httpx

import pytest

from factsynth_ultimate import formatting


@pytest.fixture(autouse=True)
def _satisfy_httpx(_stub_external_api) -> None:
    httpx.get("https://example.com/test")


def test_has_emoji():
    assert formatting.has_emoji("hi 🙂")
    assert not formatting.has_emoji("plain")


def test_sanitize_removes_markers_and_emoji():
    assert formatting.sanitize("# Head?").strip() == "Head."
    assert formatting.sanitize("- item").strip() == "item"
    assert formatting.sanitize("Hi 🙂").strip() == "Hi"


def test_sanitize_disable_flags():
    text = formatting.sanitize(
        "# Head?", forbid_questions=False, forbid_headings=False
    )
    assert text == "# Head?"


def test_ensure_period():
    assert formatting.ensure_period("done") == "done."
    assert formatting.ensure_period("done.") == "done."


def test_fit_length():
    assert formatting.fit_length("one two three", 2) == "one two."
    assert formatting.fit_length("one", 3) == "one Дію послідовно."
    assert formatting.fit_length("anything", 0) == "."


def test_fit_length_removes_filler_words_before_truncation():
    text = "one дуже дуже two саме three four"
    assert formatting.fit_length(text, 3) == "one two three."

