import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError, NotFoundError
from app.db.base import utc_now
from app.models.evaluation import EvaluationReport
from app.models.mastery import (
    AssignmentStatus,
    TrainingAssignment,
    TrainingAttempt,
    UserSkillMastery,
)
from app.models.profile import ExperienceLevel
from app.models.skill import Skill, SkillPrerequisite

logger = logging.getLogger(__name__)

ALPHA_RECENCY_WEIGHT = 0.30


class SkillMasteryEngine:
    async def record_skill_evidence(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        skill_id: uuid.UUID,
        score: float,
        evidence_confidence: float = 0.85,
    ) -> UserSkillMastery:
        """Updates user's mastery score for a skill using the exponential moving average rule:

        M_new = (1 - alpha) * M_old + alpha * S
        """
        normalized_score = max(0.0, min(1.0, score / 100.0))

        res = await db.execute(
            select(UserSkillMastery).where(
                UserSkillMastery.user_id == user_id,
                UserSkillMastery.skill_id == skill_id,
            )
        )
        record = res.scalar_one_or_none()

        if not record:
            record = UserSkillMastery(
                user_id=user_id,
                skill_id=skill_id,
                mastery_score=round(normalized_score, 4),
                confidence=round(min(1.0, evidence_confidence), 2),
                evidence_count=1,
                last_assessed_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(record)
        else:
            old_score = record.mastery_score
            new_score = (1.0 - ALPHA_RECENCY_WEIGHT) * old_score + (ALPHA_RECENCY_WEIGHT * normalized_score)
            record.mastery_score = round(max(0.0, min(1.0, new_score)), 4)
            record.evidence_count += 1
            record.confidence = round(min(1.0, record.confidence + 0.05), 2)
            record.last_assessed_at = utc_now()
            record.updated_at = utc_now()

        await db.flush()
        return record

    async def sync_report_to_mastery(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        report_id: uuid.UUID,
    ) -> list[UserSkillMastery]:
        """Iterates over all SkillEvidence items in an evaluation report and updates the user's skill mastery DAG."""
        res_rep = await db.execute(
            select(EvaluationReport)
            .options(selectinload(EvaluationReport.skill_evidences))
            .where(EvaluationReport.id == report_id)
        )
        report = res_rep.scalar_one_or_none()
        if not report:
            return []

        updated: list[UserSkillMastery] = []
        for ev in report.skill_evidences:
            m = await self.record_skill_evidence(
                db=db,
                user_id=user_id,
                skill_id=ev.skill_id,
                score=ev.score,
                evidence_confidence=ev.confidence,
            )
            updated.append(m)

        await db.commit()
        return updated

    async def generate_recommendations(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 3,
    ) -> list[TrainingAssignment]:
        """Evaluates skill mastery graph, identifies gaps or prerequisite blockers,

        and generates targeted training assignments.
        """
        # 1. Fetch all active skills and prerequisites
        all_skills = (await db.execute(select(Skill).where(Skill.is_active.is_(True)))).scalars().all()
        prereqs = (await db.execute(select(SkillPrerequisite))).scalars().all()

        # Build prerequisite adjacency: skill_id -> list of prerequisite skill_ids
        prereq_map: dict[uuid.UUID, list[uuid.UUID]] = {}
        for p in prereqs:
            prereq_map.setdefault(p.skill_id, []).append(p.prerequisite_skill_id)

        # 2. Fetch current mastery records for user
        user_mastery_res = await db.execute(
            select(UserSkillMastery).where(UserSkillMastery.user_id == user_id)
        )
        mastery_map = {m.skill_id: m.mastery_score for m in user_mastery_res.scalars().all()}

        # 3. Check existing active assignments to avoid duplicates
        active_assignments = (
            await db.execute(
                select(TrainingAssignment).where(
                    TrainingAssignment.user_id == user_id,
                    TrainingAssignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.IN_PROGRESS]),
                )
            )
        ).scalars().all()
        active_skill_ids = {a.skill_id for a in active_assignments}

        # 4. Rank skills needing practice:
        # Priority:
        # A) Assessed skills with mastery < 0.70
        # B) Unassessed foundational skills whose prerequisites are met
        candidate_skills = []
        for skill in all_skills:
            if skill.id in active_skill_ids:
                continue

            current_score = mastery_map.get(skill.id)
            prereq_ids = prereq_map.get(skill.id, [])

            # Check if prerequisites are sufficiently ready (>= 0.60)
            prereqs_ready = all(mastery_map.get(pid, 0.0) >= 0.60 for pid in prereq_ids)

            if current_score is not None and current_score < 0.70:
                # Weak skill - if its prerequisites aren't ready, prioritize the prerequisite first!
                if not prereqs_ready:
                    unready_prereq_id = next(pid for pid in prereq_ids if mastery_map.get(pid, 0.0) < 0.60)
                    prereq_skill = next((s for s in all_skills if s.id == unready_prereq_id), None)
                    if prereq_skill and prereq_skill.id not in active_skill_ids:
                        candidate_skills.append((prereq_skill, 0.95))
                else:
                    priority = 0.90 - current_score
                    candidate_skills.append((skill, priority))
            elif current_score is None and prereqs_ready:
                # Foundational or ready unassessed skill
                candidate_skills.append((skill, 0.60))

        # Sort candidate skills by priority descending
        candidate_skills.sort(key=lambda x: x[1], reverse=True)

        new_assignments: list[TrainingAssignment] = []
        for skill, _ in candidate_skills[:limit]:
            assignment = TrainingAssignment(
                user_id=user_id,
                skill_id=skill.id,
                title=f"Targeted Mastery Practice: {skill.name}",
                description=(
                    f"Drill foundational exercises, boundary conditions, and implementation patterns for {skill.name}. "
                    "Complete this assignment to elevate your skill confidence before live interviews."
                ),
                exercise_type="coding" if skill.category == "algorithms" else "conceptual",
                difficulty=ExperienceLevel.INTERMEDIATE,
                status=AssignmentStatus.PENDING,
            )
            db.add(assignment)
            new_assignments.append(assignment)

        await db.commit()

        # Return all active assignments including newly created
        res_all = await db.execute(
            select(TrainingAssignment)
            .options(selectinload(TrainingAssignment.skill))
            .where(
                TrainingAssignment.user_id == user_id,
                TrainingAssignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.IN_PROGRESS]),
            )
            .order_by(TrainingAssignment.created_at.desc())
        )
        return list(res_all.scalars().all())

    async def record_attempt(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        assignment_id: uuid.UUID,
        score: float,
        result_summary: str,
    ) -> TrainingAttempt:
        """Records an attempt on an assignment, marks assignment completed, and updates skill mastery."""
        res = await db.execute(
            select(TrainingAssignment).where(TrainingAssignment.id == assignment_id)
        )
        assignment = res.scalar_one_or_none()
        if not assignment:
            raise NotFoundError("Training assignment not found.")
        if assignment.user_id != user_id:
            raise ForbiddenError("You do not have access to this assignment.")

        attempt = TrainingAttempt(
            assignment_id=assignment_id,
            user_id=user_id,
            score=score,
            result_summary=result_summary,
            completed_at=utc_now(),
        )
        db.add(attempt)

        assignment.status = AssignmentStatus.COMPLETED
        assignment.completed_at = utc_now()

        # Update mastery score via engine
        await self.record_skill_evidence(
            db=db,
            user_id=user_id,
            skill_id=assignment.skill_id,
            score=score,
            evidence_confidence=0.90,
        )

        await db.commit()
        await db.refresh(attempt)
        return attempt


mastery_engine = SkillMasteryEngine()
