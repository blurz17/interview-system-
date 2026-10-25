import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.profile import ExperienceLevel


class CandidateProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str | None = None
    target_role: str | None = None
    experience_level: ExperienceLevel = ExperienceLevel.INTERMEDIATE
    preferred_language: str = "en"


class CandidateProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)
    target_role: str | None = Field(default=None, max_length=120)
    experience_level: ExperienceLevel | None = None
    preferred_language: str | None = Field(default=None, max_length=20)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)
    target_role: str | None = Field(default=None, max_length=120)
    experience_level: ExperienceLevel | None = ExperienceLevel.INTERMEDIATE


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    profile: CandidateProfilePublic | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=150)
    target_role: str | None = Field(default=None, max_length=120)
    experience_level: ExperienceLevel | None = None
    preferred_language: str | None = Field(default=None, max_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # in seconds


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    user: UserPublic
    tokens: TokenResponse
