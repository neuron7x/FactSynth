import os, glob, yaml, json, pytest

def test_yaml_json_parse_configs():
    paths = glob.glob("configs/**/*.yml", recursive=True) + \
            glob.glob("configs/**/*.yaml", recursive=True) + \
            glob.glob("configs/**/*.json", recursive=True)
    if not paths:
        pytest.skip("no configs to validate")
    for p in paths:
        if p.endswith((".yml", ".yaml")):
            with open(p, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        else:
            with open(p, "r", encoding="utf-8") as f:
                json.load(f)
