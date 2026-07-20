"""회원가입 요청의 검증 로직(pydantic validator)에 대한 테스트.

password/confirm_password, agree_terms 검증은 DB에 도달하기 전에
FastAPI가 422로 응답하므로, 실제 DB 상태와 무관하게 안전하게 테스트할 수 있다.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def build_signup_payload(**overrides):
    payload = {
        "full_name": "Test User",
        "username": "validation_tester",
        "password": "pw12345",
        "confirm_password": "pw12345",
        "age": 25,
        "sex": "male",
        "agree_terms": True,
    }
    payload.update(overrides)
    return payload


def test_signup_without_agreeing_to_terms_returns_422():
    response = client.post("/api/auth/signup", json=build_signup_payload(agree_terms=False))
    assert response.status_code == 422
    assert "You must agree to the terms of service" in response.text


def test_signup_with_mismatched_passwords_returns_422():
    response = client.post(
        "/api/auth/signup", json=build_signup_payload(confirm_password="different_password")
    )
    assert response.status_code == 422
    assert "Passwords do not match" in response.text
