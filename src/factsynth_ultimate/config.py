from pydantic import BaseModel
class FSUConfig(BaseModel):
    language: str = "uk"
    length: int = 100
    start_phrase: str = "Ти хочеш від мене…"
    forbid_questions: bool = True
    forbid_headings: bool = True
    forbid_lists: bool = True
    forbid_emojis: bool = True
    fallback_assumption: str = "дані частково відсутні; мета — визнання через новизну"
