FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml README.md ./
RUN pip install -U pip && pip install '.[dev]'
COPY . .
EXPOSE 8000
CMD ["uvicorn","factsynth_ultimate.app:app","--host","0.0.0.0","--port","8000"]
