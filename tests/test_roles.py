from factsynth_ultimate.glrtpm.roles import (
    Aesthete,
    Critic,
    Integrator,
    Observer,
    Rationalist,
)


def test_roles_respond() -> None:
    thesis = "X"
    assert "Formalize" in Rationalist().respond(thesis)
    assert "Counter-arguments" in Critic().respond(thesis)
    assert "Metaphor" in Aesthete().respond(thesis)
    assert "Synthesize" in Integrator().respond(thesis)
    assert "Ethics" in Observer().respond(thesis)
