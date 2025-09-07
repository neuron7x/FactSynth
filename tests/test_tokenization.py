from src.factsynth_ultimate.tokenization import count_words, tokenize


def test_tokenize_handles_punctuation() -> None:
    text = "Hello, world! state-of-the-art."
    assert tokenize(text) == ["Hello", "world", "state-of-the-art"]


def test_tokenize_handles_numeric_tokens() -> None:
    text = "Version 2.0 costs 3,000 dollars."
    assert tokenize(text) == ["Version", "2", "0", "costs", "3", "000", "dollars"]


def test_count_words_counts_numeric_tokens() -> None:
    text = "Numbers: 1, 2, and 3."
    expected = 5
    assert count_words(text) == expected
