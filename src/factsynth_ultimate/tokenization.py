import unicodedata, regex as re
_TOKEN_RE = re.compile(r"[\p{L}\p{N}ʼ'\-]+", re.UNICODE)
def normalize(text: str) -> str: return unicodedata.normalize("NFC", text)
def tokenize(text: str) -> list[str]: return _TOKEN_RE.findall(normalize(text))
def count_words(text: str) -> int: return len(tokenize(text))
