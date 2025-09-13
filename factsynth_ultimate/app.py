from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="FactSynth", version="0.1.0")


@app.get("/healthz")  # type: ignore[misc]
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")  # type: ignore[misc]
def ready() -> JSONResponse:
    return JSONResponse({"ready": True})
