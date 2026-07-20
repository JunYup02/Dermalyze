"""DB 연결 및 세션 관리 모듈."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# app.core.config가 main.py에서 먼저 임포트되어 .env를 로드해둔 상태를 전제로 한다.
# 운영 환경에서는 PostgreSQL 접속 문자열을 사용한다.
# 예: postgresql+psycopg2://user:password@localhost:5432/dermalyze
# 로컬 개발/테스트 시 DATABASE_URL을 지정하지 않으면 SQLite 파일로 대체한다.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dermalyze.db")

# SQLite는 커넥션마다 스레드 체크를 하므로 옵션을 따로 전달해야 한다.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """요청마다 DB 세션을 생성하고 종료 시 반환하는 FastAPI 의존성."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
