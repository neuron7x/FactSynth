from pathlib import Path

import yaml

MIN_JUSTIFICATION = 3
MAX_JUSTIFICATION = 7


def yload(p: str):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


def test_schema_has_contract():
    s = yload("openapi/components/schemas/FactSynthLock_v1_1.yaml")
    fs = s["components"]["schemas"]["FactSynthLock"]
    req = set(fs["required"])
    assert {"verdict", "source_synthesis", "traceability", "recommendations"} <= req

    verdict = fs["properties"]["verdict"]
    assert set(verdict["required"]) == {"status", "confidence", "summary"}
    assert set(verdict["properties"]["status"]["enum"]) == {"SUPPORTED", "REFUTED", "UNCLEAR", "OUT_OF_SCOPE", "ERROR"}

    trace = fs["properties"]["traceability"]["properties"]
    js = trace["justification_steps"]
    assert js["minItems"] == MIN_JUSTIFICATION and js["maxItems"] == MAX_JUSTIFICATION


def test_verify_ref_points_to_schema():
    v = yload("openapi/paths/verify.yaml")
    ref = v["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("#/components/schemas/FactSynthLock")
