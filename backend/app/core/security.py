"""비밀번호 해싱 및 JWT 생성/검증 로직."""
import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User

# app.core.config가 main.py에서 먼저 임포트되어 .env를 로드해둔 상태를 전제로 한다.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Swagger Authorize 팝업에 username/password 폼 대신 토큰 하나만 입력받는 칸이 뜨도록 HTTPBearer 사용
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    """평문 비밀번호를 bcrypt 해시로 변환한다."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """평문 비밀번호와 저장된 해시가 일치하는지 검증한다."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(username: str) -> str:
    """username을 payload에 담아 만료시간이 포함된 JWT를 생성한다."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"username": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """요청 헤더의 JWT를 검증하고 해당 유저를 반환한다. 만료/위조 시 401 반환."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("username")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
