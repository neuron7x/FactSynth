.PHONY: install test lint api docker

install:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install --require-hashes -r requirements.lock && pip install -e .[dev,ops]

test:
	. .venv/bin/activate && pytest

lint:
        . .venv/bin/activate && ruff check . && mypy src

api:
        . .venv/bin/activate && fsu-api

docker:
        docker build -t factsynth-ultimate:2.0 . && docker run --rm -p 8000:8000 -e API_KEY=change-me factsynth-ultimate:2.0

mutmut:
        . .venv/bin/activate && mutmut run

# Added by Incubation Pack
.PHONY: release sbom checksums test-contract

release:
	bash scripts/release/make_release.sh

sbom:
	which syft && syft packages . -o spdx-json > release/SBOM.spdx.json || echo "syft not installed"

checksums:
	cd release && sha256sum *.zip > SHA256SUMS

test-contract:
        FACTSYNTH_BASE_URL?=http://127.0.0.1:8000 \
        pytest -q tests/test_openapi_contract.py

.PHONY: scripts.calibrate scripts.fmt scripts.lint
scripts.calibrate:
	python tools/scripts_calibrate.py --root scripts --write
scripts.fmt:
	black scripts || true
	ruff check --fix scripts || true
	isort scripts || true
	shfmt -w -s -i 2 scripts || true
scripts.lint:
	ruff check scripts
	black --check scripts
	isort --check-only scripts
	shellcheck scripts/*.sh || true
