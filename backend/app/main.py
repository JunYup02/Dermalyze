from app.core import config  # noqa: F401  (loads .env before anything reads os.environ)

from fastapi import FastAPI

from app.api.routes import router as api_router

app = FastAPI(title="Dermalyze")

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
