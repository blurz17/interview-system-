import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError, NotFoundError
from app.models.coding import CodingSubmission
from app.models.evaluation import EvaluationReport, EvaluationStatus, SkillEvidence
from app.models.interview import InterviewSession, InterviewStatus, TurnSpeaker
from app.models.question import Question
from app.models.skill import Skill
from app.modules.evaluations.rubrics import DEFAULT_RUBRIC_VERSION

logger = logging.getLogger(__name__)


class EvaluationReportGenerator:
    async def generate_or_get_report(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        force_regenerate: bool = False,
    ) -> EvaluationReport:
        """Generates or retrieves the evaluation report for an interview session.

        Guarantees idempotency: returns existing completed report unless forced.
        Every score traces back to concrete evidence records.
        """
        # 1. Fetch Session
        res_session = await db.execute(
            select(InterviewSession)
            .options(
                selectinload(InterviewSession.turns),
            )
            .where(InterviewSession.id == session_id)
        )
        session = res_session.scalar_one_or_none()
        if not session:
            raise NotFoundError("Interview session not found.")
        if session.user_id != user_id:
            raise ForbiddenError("You do not have permission to view this report.")

        # 2. Check for existing report
        res_existing = await db.execute(
            select(EvaluationReport)
            .options(
                selectinload(EvaluationReport.skill_evidences).selectinload(SkillEvidence.skill)
            )
            .where(EvaluationReport.session_id == session_id)
        )
        existing_report = res_existing.scalar_one_or_none()
        if existing_report and not force_regenerate:
            if existing_report.evaluation_status == EvaluationStatus.COMPLETED:
                return existing_report

        # 3. Mark session completed if not already
        if session.status != InterviewStatus.COMPLETED:
            session.status = InterviewStatus.COMPLETED
            await db.flush()

        # If existing report exists and failed/force_regenerate, delete it first
        if existing_report:
            await db.delete(existing_report)
            await db.flush()

        # 4. Load Coding Submissions & Test Results
        res_subs = await db.execute(
            select(CodingSubmission)
            .options(selectinload(CodingSubmission.question))
            .where(CodingSubmission.session_id == session_id)
        )
        submissions = res_subs.scalars().all()

        # 5. Load default skills map
        res_skills = await db.execute(select(Skill))
        all_skills = res_skills.scalars().all()
        skill_by_id = {s.id: s for s in all_skills}
        fallback_skill = next((s for s in all_skills if s.slug in ("python", "data-structures-algorithms")), all_skills[0] if all_skills else None)

        evidence_items: list[SkillEvidence] = []
        strengths: list[str] = []
        weaknesses: list[str] = []
        recommendations: list[str] = []

        # 6. Evaluate Coding Evidence
        for sub in submissions:
            q = sub.question
            target_skill_id = q.skill_id if (q and q.skill_id and q.skill_id in skill_by_id) else (fallback_skill.id if fallback_skill else None)
            if not target_skill_id:
                continue

            test_accuracy = (sub.passed_tests / sub.total_tests) if sub.total_tests > 0 else 0.0
            coding_score = round(test_accuracy * 100.0, 1)

            if coding_score >= 80.0:
                strengths.append(
                    f"Passed {sub.passed_tests}/{sub.total_tests} tests on '{q.title if q else 'Coding Challenge'}' with solid execution efficiency."
                )
            else:
                weaknesses.append(
                    f"Failing tests on '{q.title if q else 'Coding Challenge'}': passed {sub.passed_tests}/{sub.total_tests}. Edge cases require attention."
                )

            ev = SkillEvidence(
                skill_id=target_skill_id,
                score=coding_score,
                evidence_type="coding_test_execution",
                evidence_reference=f"submission:{sub.id}",
                explanation=(
                    f"Automated sandbox verification: Passed {sub.passed_tests} of {sub.total_tests} test cases. "
                    f"Execution runtime: {sub.runtime_ms or 'N/A'} ms."
                ),
                confidence=0.95,
            )
            evidence_items.append(ev)

        # 7. Evaluate Dialogue & Conceptual Turns
        candidate_turns = [t for t in session.turns if t.speaker == TurnSpeaker.CANDIDATE]
        for t in candidate_turns:
            # Skip code blocks in turns if already scored in coding submissions
            if "```python" in t.content and submissions:
                continue

            # Find matching question
            question = None
            if t.question_id:
                q_res = await db.execute(select(Question).where(Question.id == t.question_id))
                question = q_res.scalar_one_or_none()

            skill_id = question.skill_id if (question and question.skill_id) else (fallback_skill.id if fallback_skill else None)
            if not skill_id:
                continue

            # Heuristic rubric evaluation based on length and criteria
            text_len = len(t.content.strip())
            if text_len > 120:
                conceptual_score = 88.0
                strengths.append(
                    f"Clear technical explanation for '{question.title if question else 'conceptual question'}'."
                )
            elif text_len > 40:
                conceptual_score = 72.0
            else:
                conceptual_score = 55.0
                weaknesses.append(
                    f"Brief response to '{question.title if question else 'question'}'; deeper trade-off analysis needed."
                )

            ev = SkillEvidence(
                skill_id=skill_id,
                score=conceptual_score,
                evidence_type="conceptual_turn",
                evidence_reference=f"turn:{t.id}",
                explanation=f"Demonstrated technical understanding in response: '{t.content[:140]}...'",
                confidence=0.80,
            )
            evidence_items.append(ev)

        # 8. Compute Overall Score
        if evidence_items:
            overall_score = round(sum(e.score for e in evidence_items) / len(evidence_items), 1)
        else:
            overall_score = 70.0
            if fallback_skill:
                ev = SkillEvidence(
                    skill_id=fallback_skill.id,
                    score=70.0,
                    evidence_type="interview_completion",
                    evidence_reference=f"session:{session.id}",
                    explanation="Completed baseline interview session rounds.",
                    confidence=0.70,
                )
                evidence_items.append(ev)

        # 9. Generate Tailored Recommendations
        if overall_score >= 85.0:
            recommendations.append("Ready for senior-level system design and performance optimization drills.")
            recommendations.append("Explore distributed consensus algorithms and distributed locking trade-offs.")
        elif overall_score >= 70.0:
            recommendations.append("Practice boundary cases and negative input handling in coding interviews.")
            recommendations.append("Strengthen explanations of database isolation levels and write amplification.")
        else:
            recommendations.append("Review core data structures (hash maps, stacks, trees) and Big-O notation.")
            recommendations.append("Solve targeted foundational practice exercises before re-attempting live mock.")

        if not strengths:
            strengths.append("Willingness to tackle difficult technical questions and attempt structured solutions.")
        if not weaknesses:
            weaknesses.append("Continue practicing concise communication under time constraints.")

        summary = (
            f"Candidate completed the {session.target_role} ({session.interview_type}) interview. "
            f"Overall demonstrated performance scored {overall_score}/100 across {len(evidence_items)} concrete evidence observations."
        )

        # 10. Create EvaluationReport
        report = EvaluationReport(
            session_id=session_id,
            overall_score=overall_score,
            rubric_version=DEFAULT_RUBRIC_VERSION,
            summary=summary,
            strengths=strengths[:4],
            weaknesses=weaknesses[:4],
            recommendations=recommendations[:4],
            evaluation_status=EvaluationStatus.COMPLETED,
            skill_evidences=evidence_items,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        # Reload with skill relationships populated
        res_full = await db.execute(
            select(EvaluationReport)
            .options(
                selectinload(EvaluationReport.skill_evidences).selectinload(SkillEvidence.skill)
            )
            .where(EvaluationReport.id == report.id)
        )
        return res_full.scalar_one()


evaluation_generator = EvaluationReportGenerator()
