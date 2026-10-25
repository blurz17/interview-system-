import uuid

from fastapi import APIRouter, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.core.errors import ForbiddenError, NotFoundError
from app.models.mastery import TrainingAssignment, UserSkillMastery
from app.modules.mastery.engine import mastery_engine
from app.schemas.mastery import (
    TrainingAssignmentPublic,
    TrainingAttemptCreate,
    TrainingAttemptPublic,
    UserSkillMasteryPublic,
)

router = APIRouter(tags=["Skill Mastery & Training"])


@router.get(
    "/skills/mastery",
    response_model=list[UserSkillMasteryPublic],
    status_code=status.HTTP_200_OK,
    summary="Retrieve current candidate's skill mastery profiles and confidence metrics",
)
async def get_skill_mastery(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[UserSkillMasteryPublic]:
    stmt = (
        select(UserSkillMastery)
        .options(selectinload(UserSkillMastery.skill))
        .where(UserSkillMastery.user_id == current_user.id)
        .order_by(UserSkillMastery.mastery_score.desc())
    )
    records = (await session.execute(stmt)).scalars().all()

    return [
        UserSkillMasteryPublic(
            id=rec.id,
            user_id=rec.user_id,
            skill_id=rec.skill_id,
            skill_name=rec.skill.name if rec.skill else "Unknown",
            skill_slug=rec.skill.slug if rec.skill else "unknown",
            category=rec.skill.category if rec.skill else "general",
            mastery_score=rec.mastery_score,
            confidence=rec.confidence,
            evidence_count=rec.evidence_count,
            last_assessed_at=rec.last_assessed_at,
        )
        for rec in records
    ]


@router.get(
    "/training/assignments",
    response_model=list[TrainingAssignmentPublic],
    status_code=status.HTTP_200_OK,
    summary="List training assignments assigned to current candidate",
)
async def list_training_assignments(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[TrainingAssignmentPublic]:
    stmt = (
        select(TrainingAssignment)
        .options(selectinload(TrainingAssignment.skill))
        .where(TrainingAssignment.user_id == current_user.id)
        .order_by(TrainingAssignment.created_at.desc())
    )
    records = (await session.execute(stmt)).scalars().all()

    return [
        TrainingAssignmentPublic(
            id=rec.id,
            user_id=rec.user_id,
            skill_id=rec.skill_id,
            skill_name=rec.skill.name if rec.skill else "General",
            title=rec.title,
            description=rec.description,
            exercise_type=rec.exercise_type,
            difficulty=rec.difficulty,
            status=rec.status,
            created_at=rec.created_at,
            completed_at=rec.completed_at,
        )
        for rec in records
    ]


@router.post(
    "/training/assignments/generate",
    response_model=list[TrainingAssignmentPublic],
    status_code=status.HTTP_200_OK,
    summary="Analyze skill mastery DAG and generate targeted training assignments",
)
async def generate_training_assignments(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[TrainingAssignmentPublic]:
    assignments = await mastery_engine.generate_recommendations(
        db=session,
        user_id=current_user.id,
        limit=3,
    )

    return [
        TrainingAssignmentPublic(
            id=rec.id,
            user_id=rec.user_id,
            skill_id=rec.skill_id,
            skill_name=rec.skill.name if rec.skill else "General",
            title=rec.title,
            description=rec.description,
            exercise_type=rec.exercise_type,
            difficulty=rec.difficulty,
            status=rec.status,
            created_at=rec.created_at,
            completed_at=rec.completed_at,
        )
        for rec in assignments
    ]


@router.get(
    "/training/assignments/{assignment_id}",
    response_model=TrainingAssignmentPublic,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a specific training assignment",
)
async def get_training_assignment(
    assignment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> TrainingAssignmentPublic:
    stmt = (
        select(TrainingAssignment)
        .options(selectinload(TrainingAssignment.skill))
        .where(TrainingAssignment.id == assignment_id)
    )
    assignment = (await session.execute(stmt)).scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Training assignment not found.")
    if assignment.user_id != current_user.id:
        raise ForbiddenError("You do not have permission to view this assignment.")

    return TrainingAssignmentPublic(
        id=assignment.id,
        user_id=assignment.user_id,
        skill_id=assignment.skill_id,
        skill_name=assignment.skill.name if assignment.skill else "General",
        title=assignment.title,
        description=assignment.description,
        exercise_type=assignment.exercise_type,
        difficulty=assignment.difficulty,
        status=assignment.status,
        created_at=assignment.created_at,
        completed_at=assignment.completed_at,
    )


@router.post(
    "/training/assignments/{assignment_id}/attempts",
    response_model=TrainingAttemptPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an attempt for a training assignment and update mastery scores",
)
async def submit_training_attempt(
    assignment_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    payload: TrainingAttemptCreate,
) -> TrainingAttemptPublic:
    attempt = await mastery_engine.record_attempt(
        db=session,
        user_id=current_user.id,
        assignment_id=assignment_id,
        score=payload.score,
        result_summary=payload.result_summary,
    )
    return TrainingAttemptPublic.model_validate(attempt)
