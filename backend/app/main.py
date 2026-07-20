from app.core import config  # noqa: F401  (loads .env before anything reads os.environ)

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.database import Base, engine

app = FastAPI(title="Dermalyze")

# 프론트엔드 도메인은 환경변수로 관리한다. 개발 중에는 콤마로 구분된 "*"를 허용.
allowed_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "*")
allowed_origins = (
    ["*"] if allowed_origins_env.strip() == "*" else [o.strip() for o in allowed_origins_env.split(",")]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 앱 시작 시 정의된 모델(User)에 대해 테이블을 자동 생성한다.
Base.metadata.create_all(bind=engine)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
