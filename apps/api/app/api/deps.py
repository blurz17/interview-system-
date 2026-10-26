import uuid
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.modules.auth.service import AuthService

settings = get_settings()

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str | None, Depends(reusable_oauth2)]


async def get_current_user(
    session: SessionDep,
    token: TokenDep,
) -> User:
    if not token:
        raise UnauthorizedError("Not authenticated")

    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedError("Could not validate credentials")
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise UnauthorizedError("Could not validate credentials") from None

    auth_service = AuthService(session)
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Inactive user account")

    return user


async def get_current_user_optional(
    session: SessionDep,
    token: TokenDep,
) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_id = uuid.UUID(user_id_str)
        auth_service = AuthService(session)
        user = await auth_service.get_user_by_id(user_id)
        return user if user and user.is_active else None
    except Exception:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]

