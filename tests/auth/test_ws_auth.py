import pytest

from factsynth_ultimate.auth import ws


@pytest.fixture(autouse=True)
def _reset_registry():
    ws.reset_ws_registry()
    yield
    ws.reset_ws_registry()


def test_authenticate_ws_success():
    user = ws.WebSocketUser(api_key="alpha", organization="team", status="active")
    ws.set_ws_registry({user.api_key: user})

    authenticated = ws.authenticate_ws("alpha")

    assert authenticated is user
    assert authenticated.organization == "team"


def test_authenticate_ws_missing_key():
    with pytest.raises(ws.WebSocketAuthError) as excinfo:
        ws.authenticate_ws("")

    err = excinfo.value
    assert err.code == 4401
    assert "Missing" in err.reason


def test_authenticate_ws_unknown_key():
    ws.set_ws_registry({})

    with pytest.raises(ws.WebSocketAuthError) as excinfo:
        ws.authenticate_ws("does-not-exist")

    assert excinfo.value.code == 4401


def test_authenticate_ws_requires_organization():
    user = ws.WebSocketUser(api_key="beta", organization="", status="active")
    ws.set_ws_registry({user.api_key: user})

    with pytest.raises(ws.WebSocketAuthError) as excinfo:
        ws.authenticate_ws("beta")

    assert excinfo.value.code == 4403


def test_authenticate_ws_requires_active_status():
    user = ws.WebSocketUser(api_key="gamma", organization="org", status="disabled")
    ws.set_ws_registry({user.api_key: user})

    with pytest.raises(ws.WebSocketAuthError) as excinfo:
        ws.authenticate_ws("gamma")

    assert excinfo.value.code == 4429


def test_authenticate_ws_case_insensitive_lookup():
    user = ws.WebSocketUser(api_key="DeltaKey", organization="org", status="active")
    ws.set_ws_registry({user.api_key: user})

    authenticated = ws.authenticate_ws("deltakey")

    assert authenticated is user
