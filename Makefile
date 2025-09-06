.PHONY: install test lint api docker

install:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e .[dev,ops]

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check . && mypy src

api:
	. .venv/bin/activate && fsu-api

docker:
	docker build -t factsynth-ultimate:2.0 . && docker run --rm -p 8000:8000 -e API_KEY=change-me factsynth-ultimate:2.0
