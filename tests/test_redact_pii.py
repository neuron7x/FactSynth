
from factsynth_ultimate.services.evaluator import evaluate_claim
from factsynth_ultimate.services.redaction import redact_pii
from factsynth_ultimate.services.retrievers.base import RetrievedDoc

def test_redact_email():
    text = "Contact me at test@example.com for details."
    assert redact_pii(text) == "Contact me at [REDACTED_EMAIL] for details."

def test_redact_phone():
    text = "Call me at 123-456-7890 tomorrow."
    assert redact_pii(text) == "Call me at [REDACTED_PHONE] tomorrow."

def test_redact_ssn():
    text = "SSN 123-45-6789 should be private."
    assert redact_pii(text) == "SSN [REDACTED_SSN] should be private."

def test_evaluate_claim_redacts_evidence_content():
    class DummyRetriever:
        def search(self, q):
            return [RetrievedDoc(id="src", text="Email test@example.com now", score=1.0)]

        def close(self):  # pragma: no cover - no-op
            pass

    result = evaluate_claim("alpha", retriever=DummyRetriever())
    assert result["evidence"][0]["content"] == "Email [REDACTED_EMAIL] now"
