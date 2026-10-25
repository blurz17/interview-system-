import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, SessionDep
from app.modules.coding.service import coding_service
from app.schemas.coding import (
    CodingSubmissionCreate,
    CodingSubmissionPublic,
    TestResultPublic,
)

router = APIRouter(tags=["Coding"])


@router.post(
    "/interviews/{session_id}/submissions",
    response_model=CodingSubmissionPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Submit candidate source code for execution and evaluation",
)
async def submit_code(
    session_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    payload: CodingSubmissionCreate,
) -> CodingSubmissionPublic:
    sub = await coding_service.submit_code(
        db=session,
        session_id=session_id,
        user_id=current_user.id,
        payload=payload,
    )
    return CodingSubmissionPublic.model_validate(sub)


@router.get(
    "/submissions/{submission_id}",
    response_model=CodingSubmissionPublic,
    status_code=status.HTTP_200_OK,
    summary="Get execution status and summary stats of a submission",
)
async def get_submission(
    submission_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> CodingSubmissionPublic:
    sub = await coding_service.get_submission(
        db=session,
        submission_id=submission_id,
        user_id=current_user.id,
    )
    return CodingSubmissionPublic.model_validate(sub)


@router.get(
    "/submissions/{submission_id}/results",
    response_model=list[TestResultPublic],
    status_code=status.HTTP_200_OK,
    summary="Get candidate-safe test results (hidden test inputs/outputs redacted)",
)
async def get_submission_results(
    submission_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[TestResultPublic]:
    return await coding_service.get_candidate_safe_results(
        db=session,
        submission_id=submission_id,
        user_id=current_user.id,
    )
