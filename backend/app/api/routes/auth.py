"""회원가입 / 로그인 라우터."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, SignupResponse, TokenResponse

router = APIRouter(prefix="/auth")


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """회원가입: username 중복 체크 후 비밀번호를 해싱하여 저장한다."""
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    user = User(
        username=request.username,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        age=request.age,
        sex=request.sex,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """로그인: username/password 검증 후 JWT를 발급한다."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid username or password",
    )

    user = db.query(User).filter(User.username == request.username).first()
    if user is None or not verify_password(request.password, user.password_hash):
        raise unauthorized

    access_token = create_access_token(username=user.username)
    return TokenResponse(access_token=access_token)
