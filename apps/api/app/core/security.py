from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(f"{password}{settings.password_pepper}")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, f"{password}{settings.password_pepper}")
    except VerifyMismatchError:
        return False


def create_token(user_id: UUID, email: str, role: str, token_type: str) -> str:
    ttl = (
        settings.jwt_access_ttl_seconds
        if token_type == "access"
        else settings.jwt_refresh_ttl_seconds
    )
    secret = settings.jwt_access_secret if token_type == "access" else settings.jwt_refresh_secret
    now = datetime.now(UTC)
    payload = {
        "iss": settings.jwt_issuer,
        "sub": str(user_id),
        "email": email,
        "role": role,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=ttl)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, token_type: str) -> dict[str, str]:
    secret = settings.jwt_access_secret if token_type == "access" else settings.jwt_refresh_secret
    payload = jwt.decode(
        token,
        secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "iat", "iss", "sub", "type"]},
    )
    if payload.get("type") != token_type:
        raise jwt.InvalidTokenError("Invalid token type")
    return payload

