import uuid

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import ForbiddenError, NotFoundError
from app.models.interview import InterviewSession
from app.modules.interviews.orchestrator import InterviewOrchestrator
from app.schemas.interview import (
    InterviewCreate,
    InterviewDetail,
    InterviewPublic,
    InterviewTurnCreate,
    InterviewTurnPublic,
)

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post("", response_model=InterviewPublic, status_code=status.HTTP_201_CREATED)
async def create_interview(
    session: SessionDep,
    current_user: CurrentUser,
    payload: InterviewCreate,
) -> InterviewPublic:
    new_session = InterviewSession(
        user_id=current_user.id,
        target_role=payload.target_role,
        interview_type=payload.interview_type,
        interaction_mode=payload.interaction_mode,
        difficulty=payload.difficulty,
        resume_id=payload.resume_id,
    )
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    return InterviewPublic.model_validate(new_session)


@router.get("", response_model=list[InterviewPublic], status_code=status.HTTP_200_OK)
async def list_interviews(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[InterviewPublic]:
    stmt = (
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.created_at.desc())
    )
    sessions = (await session.execute(stmt)).scalars().all()
    return [InterviewPublic.model_validate(s) for s in sessions]


@router.get("/{session_id}", response_model=InterviewDetail, status_code=status.HTTP_200_OK)
async def get_interview(
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> InterviewDetail:
    orchestrator = InterviewOrchestrator(session)
    interview_session = await orchestrator.get_session_by_id(session_id)
    if not interview_session:
        raise NotFoundError("Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this interview session.")

    return InterviewDetail(
        id=interview_session.id,
        target_role=interview_session.target_role,
        interview_type=interview_session.interview_type,
        interaction_mode=interview_session.interaction_mode,
        difficulty=interview_session.difficulty,
        status=interview_session.status,
        resume_id=interview_session.resume_id,
        started_at=interview_session.started_at,
        completed_at=interview_session.completed_at,
        created_at=interview_session.created_at,
        turns=[InterviewTurnPublic.model_validate(t) for t in interview_session.turns],
    )


@router.post(
    "/{session_id}/start", response_model=InterviewTurnPublic, status_code=status.HTTP_200_OK
)
async def start_interview(
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> InterviewTurnPublic:
    orchestrator = InterviewOrchestrator(session)
    interview_session = await orchestrator.get_session_by_id(session_id)
    if not interview_session:
        raise NotFoundError("Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this interview session.")

    turn = await orchestrator.start_session(interview_session)
    return InterviewTurnPublic.model_validate(turn)


@router.post(
    "/{session_id}/turns", response_model=InterviewTurnPublic, status_code=status.HTTP_200_OK
)
async def submit_turn(
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
    payload: InterviewTurnCreate,
) -> InterviewTurnPublic:
    orchestrator = InterviewOrchestrator(session)
    interview_session = await orchestrator.get_session_by_id(session_id)
    if not interview_session:
        raise NotFoundError("Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this interview session.")

    assistant_turn = await orchestrator.process_candidate_turn(
        interview_session,
        payload.content,
        payload.input_mode,
    )
    return InterviewTurnPublic.model_validate(assistant_turn)


@router.get(
    "/{session_id}/turns", response_model=list[InterviewTurnPublic], status_code=status.HTTP_200_OK
)
async def get_turns(
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> list[InterviewTurnPublic]:
    stmt = (
        select(InterviewSession)
        .where(InterviewSession.id == session_id)
        .options(selectinload(InterviewSession.turns))
    )
    interview_session = (await session.execute(stmt)).scalar_one_or_none()
    if not interview_session:
        raise NotFoundError("Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this interview session.")

    return [InterviewTurnPublic.model_validate(t) for t in interview_session.turns]


@router.post(
    "/{session_id}/complete", response_model=InterviewPublic, status_code=status.HTTP_200_OK
)
async def complete_interview(
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> InterviewPublic:
    orchestrator = InterviewOrchestrator(session)
    interview_session = await orchestrator.get_session_by_id(session_id)
    if not interview_session:
        raise NotFoundError("Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this interview session.")

    completed = await orchestrator.complete_session(interview_session)
    return InterviewPublic.model_validate(completed)


@router.post(
    "/{session_id}/abandon", response_model=InterviewPublic, status_code=status.HTTP_200_OK
)
async def abandon_interview(
    session: SessionDep,
    current_user: CurrentUser,
    session_id: uuid.UUID,
) -> InterviewPublic:
    orchestrator = InterviewOrchestrator(session)
    interview_session = await orchestrator.get_session_by_id(session_id)
    if not interview_session:
        raise NotFoundError("Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise ForbiddenError("You do not have access to this interview session.")

    abandoned = await orchestrator.abandon_session(interview_session)
    return InterviewPublic.model_validate(abandoned)
