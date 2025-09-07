FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --upgrade pip && pip install -e .[test]
EXPOSE 8000
CMD ["uvicorn","factsynth_ultimate.app:app","--host","0.0.0.0","--port","8000"]
