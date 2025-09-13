.PHONY: setup fmt lint type test cov run docs build docker-build docker-run
setup:
python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements-dev.txt -e .
fmt:
ruff format .
lint:
ruff check .
type:
mypy .
test:
pytest
cov:
pytest --cov=. --cov-config=coverage.toml
run:
uvicorn factsynth_ultimate.app:app --host 0.0.0.0 --port 8000 --reload
docs:
mkdocs build --strict
build:
python -m build
docker-build:
docker build -t factsynth:dev .
docker-run:
docker run --rm -p 8000:8000 factsynth:dev
