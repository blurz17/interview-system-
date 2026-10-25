import uuid

from fastapi import APIRouter, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import SessionDep
from app.core.errors import NotFoundError
from app.models.profile import ExperienceLevel
from app.models.skill import Skill
from app.schemas.skill import SkillPublic

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=list[SkillPublic], status_code=status.HTTP_200_OK)
async def list_skills(
    session: SessionDep,
    category: str | None = Query(None, description="Filter by skill category"),
    difficulty: ExperienceLevel | None = Query(None, description="Filter by difficulty level"),
) -> list[SkillPublic]:
    stmt = (
        select(Skill)
        .where(Skill.is_active.is_(True))
        .options(selectinload(Skill.prerequisites))
        .order_by(Skill.category, Skill.name)
    )
    if category:
        stmt = stmt.where(Skill.category == category)
    if difficulty:
        stmt = stmt.where(Skill.difficulty_level == difficulty)

    skills = (await session.execute(stmt)).scalars().all()
    return [SkillPublic.model_validate(s) for s in skills]


@router.get("/{skill_id}", response_model=SkillPublic, status_code=status.HTTP_200_OK)
async def get_skill(session: SessionDep, skill_id: uuid.UUID) -> SkillPublic:
    stmt = (
        select(Skill)
        .where(Skill.id == skill_id, Skill.is_active.is_(True))
        .options(selectinload(Skill.prerequisites))
    )
    skill = (await session.execute(stmt)).scalar_one_or_none()
    if not skill:
        raise NotFoundError("Skill not found.")
    return SkillPublic.model_validate(skill)
