from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.modules.auth.service import AuthService
from app.schemas.user import (
    AuthResponse,
    TokenRefreshRequest,
    UserLogin,
    UserPublic,
    UserRegister,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate account",
)
async def register(session: SessionDep, payload: UserRegister) -> AuthResponse:
    auth_service = AuthService(session)
    user = await auth_service.register_user(payload)
    tokens = await auth_service.create_tokens(user)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate candidate credentials",
)
async def login(session: SessionDep, payload: UserLogin) -> AuthResponse:
    auth_service = AuthService(session)
    user = await auth_service.authenticate_user(payload.email, payload.password)
    tokens = await auth_service.create_tokens(user)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_token(session: SessionDep, payload: TokenRefreshRequest) -> AuthResponse:
    auth_service = AuthService(session)
    user, tokens = await auth_service.rotate_refresh_token(payload.refresh_token)
    return AuthResponse(user=UserPublic.model_validate(user), tokens=tokens)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token session",
)
async def logout(session: SessionDep, payload: TokenRefreshRequest):
    auth_service = AuthService(session)
    await auth_service.revoke_refresh_token(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile",
)
async def get_current_user_profile(current_user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="Update current candidate profile",
)
async def update_current_user_profile(
    session: SessionDep,
    current_user: CurrentUser,
    payload: UserUpdate,
) -> UserPublic:
    profile = current_user.profile
    if profile:
        if payload.full_name is not None:
            profile.full_name = payload.full_name
        if payload.target_role is not None:
            profile.target_role = payload.target_role
        if payload.experience_level is not None:
            profile.experience_level = payload.experience_level
        if payload.preferred_language is not None:
            profile.preferred_language = payload.preferred_language

    await session.commit()
    await session.refresh(current_user, attribute_names=["profile"])
    return UserPublic.model_validate(current_user)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account and data",
)
async def delete_current_user_account(session: SessionDep, current_user: CurrentUser):
    await session.delete(current_user)
    await session.commit()
