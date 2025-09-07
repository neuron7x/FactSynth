from pydantic import BaseModel


class FSUConfig(BaseModel):
    """Runtime configuration for FactSynth Ultimate.

    Attributes:
        language: Output language code. Defaults to ``"uk"``.
        length: Target number of words in the generated insight. Defaults to ``100``.
        start_phrase: Text prepended to every generated insight. Defaults to
            ``"Ти хочеш від мене…"``.
        forbid_questions: If ``True``, question marks are disallowed. Defaults to ``True``.
        forbid_headings: If ``True``, heading formatting is removed. Defaults to ``True``.
        forbid_lists: If ``True``, bullet or numbered lists are disallowed. Defaults to ``True``.
        forbid_emojis: If ``True``, emoji characters are stripped. Defaults to ``True``.
        fallback_assumption: Placeholder assumption used when input data is incomplete.
            Defaults to ``"дані частково відсутні; мета — визнання через новизну"``.
    """

    language: str = "uk"
    length: int = 100
    start_phrase: str = "Ти хочеш від мене…"
    forbid_questions: bool = True
    forbid_headings: bool = True
    forbid_lists: bool = True
    forbid_emojis: bool = True
    fallback_assumption: str = "дані частково відсутні; мета — визнання через новизну"
