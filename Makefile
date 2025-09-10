.PHONY: install test fmt lint api docker release sbom checksums test-contract scripts.upgrade

install:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e .[dev,ops]

test:
	. .venv/bin/activate && pytest

fmt:
	black .
	ruff check --fix .
	isort .

lint:
	ruff check .
	black --check .
	isort --check-only .
	shfmt -d -s -i 2 scripts
	shellcheck scripts/*.sh scripts/release/make_release.sh || true
	mypy src

api:
	. .venv/bin/activate && fsu-api

docker:
	docker build -t factsynth-ultimate:2.0 . && docker run --rm -p 8000:8000 -e API_KEY=change-me factsynth-ultimate:2.0

# Added by Incubation Pack
release:
	bash scripts/release/make_release.sh

sbom:
	which syft && syft packages . -o spdx-json > release/SBOM.spdx.json || echo "syft not installed"

checksums:
	cd release && sha256sum *.zip > SHA256SUMS

test-contract:
	FACTSYNTH_BASE_URL?=http://127.0.0.1:8000 \
	pytest -q tests/test_openapi_contract.py

scripts.upgrade:
	python tools/modernize_py_scripts.py --root scripts --write
	python tools/modernize_shell_scripts.py --root scripts --write
