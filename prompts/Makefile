.PHONY: lint validate schema

lint:
	npx prettier@3.3.3 --check .

schema:
	npx ajv-cli@5.0.0 compile --strict=true -s SCHEMAS/*.schema.json
	npx ajv-cli@5.0.0 validate --strict=true -s SCHEMAS/golden_12.schema.json -d GOLDEN_12_TESTSET.json

validate: schema
	sha256sum -c SHASUMS256.txt
