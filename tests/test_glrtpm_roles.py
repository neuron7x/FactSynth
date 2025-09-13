import pytest

from factsynth_ultimate.glrtpm.roles import (
    Aesthete,
    Critic,
    Integrator,
    Observer,
    Rationalist,
)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_roles_respond_include_name_and_thesis():
    thesis = "test case"
    roles = [Rationalist(), Critic(), Aesthete(), Integrator(), Observer()]
    for role in roles:
        resp = role.respond(thesis)
        assert thesis in resp
        assert role.name in resp
