import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.base import utc_now
from app.models.profile import CandidateProfile, ExperienceLevel
from app.models.token import RefreshToken
from app.models.user import User
from app.schemas.user import TokenResponse, UserRegister

settings = get_settings()


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        normalized_email = email.strip().lower()
        stmt = (
            select(User).where(User.email == normalized_email).options(selectinload(User.profile))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.profile))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def register_user(self, payload: UserRegister) -> User:
        normalized_email = payload.email.strip().lower()

        # Check existing email
        existing = await self.get_user_by_email(normalized_email)
        if existing:
            raise ConflictError("An account with this email address already exists.")

        # Hash password
        pwd_hash = hash_password(payload.password)

        # Create user
        new_user = User(
            email=normalized_email,
            password_hash=pwd_hash,
            is_active=True,
        )
        self.db.add(new_user)
        await self.db.flush()

        # Create default candidate profile
        profile = CandidateProfile(
            user_id=new_user.id,
            full_name=payload.full_name,
            target_role=payload.target_role,
            experience_level=payload.experience_level or ExperienceLevel.INTERMEDIATE,
            preferred_language="en",
        )
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(new_user, attribute_names=["profile"])
        return new_user

    async def authenticate_user(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        user = await self.get_user_by_email(normalized_email)

        # Constant-time mitigation against timing attacks
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")

        if not user.is_active:
            raise UnauthorizedError("User account is inactive.")

        return user

    async def create_tokens(self, user: User) -> TokenResponse:
        # Access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            expires_delta=access_token_expires,
            additional_claims={"email": user.email},
        )

        # Cryptographically secure random refresh token
        raw_refresh_token = secrets.token_urlsafe(48)
        hashed_rt = hash_token(raw_refresh_token)
        refresh_expires = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        db_token = RefreshToken(
            user_id=user.id,
            token_hash=hashed_rt,
            expires_at=refresh_expires,
        )
        self.db.add(db_token)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
        )

    async def rotate_refresh_token(self, raw_refresh_token: str) -> tuple[User, TokenResponse]:
        hashed_rt = hash_token(raw_refresh_token)

        stmt = (
            select(RefreshToken)
            .where(RefreshToken.token_hash == hashed_rt)
            .options(selectinload(RefreshToken.user).selectinload(User.profile))
        )
        result = await self.db.execute(stmt)
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise UnauthorizedError("Invalid refresh token.")

        # If token was already revoked, this indicates a reuse attempt!
        # Revoke the entire token family for this user to protect against stolen tokens.
        if token_record.revoked_at is not None:
            now = utc_now()
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == token_record.user_id)
                .values(revoked_at=now)
            )
            await self.db.commit()
            raise UnauthorizedError(
                "Revoked refresh token reuse detected. All sessions terminated."
            )

        now = utc_now()
        # Verify expiry
        if ensure_utc(token_record.expires_at) <= now:
            raise UnauthorizedError("Refresh token has expired. Please sign in again.")

        user = token_record.user
        if not user or not user.is_active:
            raise UnauthorizedError("User is inactive or not found.")

        # Generate new tokens
        new_tokens = await self.create_tokens(user)
        new_hashed_rt = hash_token(new_tokens.refresh_token)

        # Find the new token ID to link replaced_by_id
        stmt_new = select(RefreshToken.id).where(RefreshToken.token_hash == new_hashed_rt)
        new_token_id = (await self.db.execute(stmt_new)).scalar_one()

        # Mark previous token as revoked and set replacement
        token_record.revoked_at = now
        token_record.replaced_by_id = new_token_id
        await self.db.commit()

        return user, new_tokens

    async def revoke_refresh_token(self, raw_refresh_token: str) -> None:
        hashed_rt = hash_token(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed_rt)
        result = await self.db.execute(stmt)
        token_record = result.scalar_one_or_none()

        if token_record and token_record.revoked_at is None:
            token_record.revoked_at = utc_now()
            await self.db.commit()
