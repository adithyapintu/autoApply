from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, UowDep
from app.core.security import decode_token
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    UserResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()


def serialize_user(user) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_email_verified=user.is_email_verified,
    )


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, uow: UowDep) -> TokenPair:
    _, tokens = await AuthService(uow).register(payload.email, payload.password, payload.full_name)
    return tokens


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, uow: UowDep) -> TokenPair:
    return await AuthService(uow).login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenPair)
async def refresh(refresh_token: str, uow: UowDep) -> TokenPair:
    payload = decode_token(refresh_token, "refresh")
    user = await uow.users.find_by_email(payload["email"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    return AuthService(uow).issue_tokens(user)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(_: ForgotPasswordRequest) -> dict[str, str]:
    return {"status": "accepted"}


@router.post("/reset-password", status_code=status.HTTP_202_ACCEPTED)
async def reset_password(_: ResetPasswordRequest) -> dict[str, str]:
    return {"status": "accepted"}


@router.post("/verify-email", status_code=status.HTTP_202_ACCEPTED)
async def verify_email(token: str) -> dict[str, str]:
    return {"status": "accepted", "token": token[:8]}


@router.get("/google/login")
async def google_login() -> dict[str, str]:
    return {"status": "configure_google_oauth_client"}


@router.get("/google/callback")
async def google_callback(code: str) -> dict[str, str]:
    return {"status": "accepted", "code": code[:8]}


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return serialize_user(current_user)
