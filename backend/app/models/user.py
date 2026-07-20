"""SQLAlchemy ORM 모델 정의."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class User(Base):
    """회원 정보를 저장하는 users 테이블."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)  # 로그인 ID
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)  # 실명
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)  # "male" / "female" / "prefer_not_to_say"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
