"""회원가입/로그인 관련 Pydantic 스키마."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

Sex = Literal["male", "female", "prefer_not_to_say"]


class SignupRequest(BaseModel):
    full_name: str
    username: str
    password: str
    confirm_password: str  # DB에 저장하지 않고 비밀번호 확인용으로만 사용
    age: int
    sex: Sex
    agree_terms: bool

    @field_validator("age")
    @classmethod
    def validate_age_range(cls, value: int) -> int:
        """나이는 1~120 범위만 허용한다."""
        if not 1 <= value <= 120:
            raise ValueError("age must be between 1 and 120")
        return value

    @model_validator(mode="after")
    def validate_passwords_and_terms(self) -> "SignupRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if not self.agree_terms:
            raise ValueError("You must agree to the terms of service")
        return self


class SignupResponse(BaseModel):
    id: int
    username: str
    full_name: str
    age: int
    sex: Sex
    created_at: datetime

    # password, confirm_password, password_hash는 절대 포함하지 않는다.
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
