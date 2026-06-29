from uuid import uuid4

from app.core.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_access_token_roundtrip() -> None:
    user_id = uuid4()
    token = create_token(user_id, "user@example.com", "user", "access")
    payload = decode_token(token, "access")

    assert payload["sub"] == str(user_id)
    assert payload["email"] == "user@example.com"
    assert payload["type"] == "access"

