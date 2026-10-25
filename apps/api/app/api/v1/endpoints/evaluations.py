import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.modules.evaluations.generator import evaluation_generator
from app.schemas.evaluation import EvaluationReportPublic, SkillEvidencePublic

router = APIRouter(tags=["Evaluations"])


def _to_report_public(report) -> EvaluationReportPublic:
    evidences_public = []
    for ev in report.skill_evidences:
        evidences_public.append(
            SkillEvidencePublic(
                id=ev.id,
                skill_id=ev.skill_id,
                skill_name=ev.skill.name if ev.skill else "General Assessment",
                skill_slug=ev.skill.slug if ev.skill else "general",
                score=ev.score,
                evidence_type=ev.evidence_type,
                evidence_reference=ev.evidence_reference,
                explanation=ev.explanation,
                confidence=ev.confidence,
                created_at=ev.created_at,
            )
        )

    return EvaluationReportPublic(
        id=report.id,
        session_id=report.session_id,
        overall_score=report.overall_score,
        rubric_version=report.rubric_version,
        summary=report.summary,
        strengths=report.strengths,
        weaknesses=report.weaknesses,
        recommendations=report.recommendations,
        evaluation_status=report.evaluation_status,
        skill_evidences=evidences_public,
        created_at=report.created_at,
    )


@router.get(
    "/interviews/{session_id}/report",
    response_model=EvaluationReportPublic,
    status_code=status.HTTP_200_OK,
    summary="Retrieve completed evaluation report and traceable evidence for an interview session",
)
async def get_interview_report(
    session_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> EvaluationReportPublic:
    report = await evaluation_generator.generate_or_get_report(
        db=session,
        session_id=session_id,
        user_id=current_user.id,
        force_regenerate=False,
    )
    return _to_report_public(report)


@router.post(
    "/interviews/{session_id}/evaluate",
    response_model=EvaluationReportPublic,
    status_code=status.HTTP_200_OK,
    summary="Evaluate or re-evaluate an interview session and generate the performance scorecard",
)
async def evaluate_interview_session(
    session_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> EvaluationReportPublic:
    report = await evaluation_generator.generate_or_get_report(
        db=session,
        session_id=session_id,
        user_id=current_user.id,
        force_regenerate=True,
    )
    return _to_report_public(report)
