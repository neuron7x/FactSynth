from http import HTTPStatus

import pytest

PROBLEM_KEYS = {"detail"}


@pytest.mark.anyio
async def test_problem_json_shape_on_validation_error(client, base_headers):
    r = await client.post("/v1/score", headers=base_headers, json={"text": 123})
    assert r.status_code in (
        HTTPStatus.BAD_REQUEST,
        HTTPStatus.UNPROCESSABLE_ENTITY,
    )
    body = r.json()
    assert PROBLEM_KEYS.issubset(body.keys())
