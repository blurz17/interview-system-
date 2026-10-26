import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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
    password: str = Field(min_length=6, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)
    target_role: str | None = Field(default=None, max_length=120)
    experience_level: ExperienceLevel | None = ExperienceLevel.INTERMEDIATE

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("full_name", "target_role", mode="before")
    @classmethod
    def strip_optional_strings(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            val = v.strip()
            return val if val else None
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v


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
