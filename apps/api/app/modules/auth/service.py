from fastapi import HTTPException, status

from app.core.security import create_token, hash_password, verify_password
from app.db.models import User
from app.db.repositories import UnitOfWork
from app.modules.auth.schemas import TokenPair


class AuthService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def register(self, email: str, password: str, full_name: str | None) -> tuple[User, TokenPair]:
        existing = await self.uow.users.find_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = await self.uow.users.create(email, hash_password(password), full_name)
        await self.uow.commit()
        return user, self.issue_tokens(user)

    async def login(self, email: str, password: str) -> TokenPair:
        user = await self.uow.users.find_by_email(email)
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return self.issue_tokens(user)

    def issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=create_token(user.id, user.email, user.role, "access"),
            refresh_token=create_token(user.id, user.email, user.role, "refresh"),
        )

