import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utc_now
from app.models.profile import ExperienceLevel


class SkillPrerequisite(Base):
    __tablename__ = "skill_prerequisites"
    __table_args__ = (
        CheckConstraint("skill_id != prerequisite_skill_id", name="check_no_self_prerequisite"),
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    prerequisite_skill_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        index=True,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    category: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
    )
    difficulty_level: Mapped[ExperienceLevel] = mapped_column(
        Enum(ExperienceLevel, name="experience_level_enum", native_enum=False),
        default=ExperienceLevel.INTERMEDIATE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # DAG Prerequisites
    prerequisites: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="skill_prerequisites",
        primaryjoin="Skill.id == SkillPrerequisite.skill_id",
        secondaryjoin="Skill.id == SkillPrerequisite.prerequisite_skill_id",
        back_populates="dependents",
    )
    dependents: Mapped[list["Skill"]] = relationship(
        "Skill",
        secondary="skill_prerequisites",
        primaryjoin="Skill.id == SkillPrerequisite.prerequisite_skill_id",
        secondaryjoin="Skill.id == SkillPrerequisite.skill_id",
        back_populates="prerequisites",
    )
