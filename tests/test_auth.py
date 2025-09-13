import os
import string
from http import HTTPStatus

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

API_KEY = os.getenv("API_KEY", "change-me")


@st.composite
def header_variations(draw):
    name_flags = draw(st.lists(st.booleans(), min_size=len("x-api-key"), max_size=len("x-api-key")))
    name = "".join(
        c.upper() if flag else c.lower() for c, flag in zip("x-api-key", name_flags, strict=False)
    )
    value_flags = draw(st.lists(st.booleans(), min_size=len(API_KEY), max_size=len(API_KEY)))
    value = "".join(
        c.upper() if flag else c.lower() for c, flag in zip(API_KEY, value_flags, strict=False)
    )
    return name, value


@pytest.mark.anyio
@given(header_variations())
async def test_api_key_case_insensitive(client, header_variations):
    name, value = header_variations
    r = await client.post(
        "/v1/generate", headers={name: value}, json={"text": "hello"}
    )
    assert r.status_code == HTTPStatus.OK


@st.composite
def invalid_keys(draw):
    alphabet = string.ascii_letters + string.digits
    key = draw(
        st.text(alphabet=alphabet, min_size=len(API_KEY), max_size=len(API_KEY))
    )
    assume(key.casefold() != API_KEY.casefold())
    return key


@pytest.mark.anyio
@given(invalid_keys())
async def test_invalid_key_rejected(client, invalid_keys):
    key = invalid_keys
    r = await client.post(
        "/v1/generate", headers={"x-api-key": key}, json={"text": "hi"}
    )
    assert r.status_code == HTTPStatus.FORBIDDEN
