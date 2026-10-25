import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.integrations.judge0.client import judge0_client
from app.models.coding import (
    CodingSubmission,
    ExecutionStatus,
    QuestionTestCase,
    TestResult,
    TestResultStatus,
)
from app.models.interview import InterviewSession, InterviewStatus, InterviewTurn, TurnSpeaker
from app.models.question import Question
from app.schemas.coding import CodingSubmissionCreate, TestResultPublic

logger = logging.getLogger(__name__)


class CodingService:
    async def submit_code(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        payload: CodingSubmissionCreate,
    ) -> CodingSubmission:
        """Submits candidate source code, executes it against question test cases via Judge0,

        and records traceable test results.
        """
        # 1. Validate session
        res_session = await db.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        session = res_session.scalar_one_or_none()
        if not session:
            raise NotFoundError("Interview session not found.")
        if session.user_id != user_id:
            raise ForbiddenError("You do not have access to this interview session.")
        if session.status != InterviewStatus.IN_PROGRESS:
            raise BadRequestError(f"Cannot submit code to a session with status '{session.status}'.")

        # 2. Check Idempotency Key
        if payload.idempotency_key:
            res_existing = await db.execute(
                select(CodingSubmission)
                .options(selectinload(CodingSubmission.test_results))
                .where(
                    CodingSubmission.session_id == session_id,
                    CodingSubmission.idempotency_key == payload.idempotency_key,
                )
            )
            existing_sub = res_existing.scalar_one_or_none()
            if existing_sub:
                logger.info(f"Returning idempotent submission {existing_sub.id}")
                return existing_sub

        # 3. Validate Question
        res_q = await db.execute(
            select(Question)
            .options(selectinload(Question.test_cases))
            .where(Question.id == payload.question_id)
        )
        question = res_q.scalar_one_or_none()
        if not question:
            raise NotFoundError("Question not found.")

        # 4. Create Initial Submission Record
        submission = CodingSubmission(
            session_id=session_id,
            question_id=payload.question_id,
            user_id=user_id,
            language_id=payload.language_id,
            source_code=payload.source_code,
            idempotency_key=payload.idempotency_key,
            execution_status=ExecutionStatus.RUNNING,
            passed_tests=0,
            total_tests=0,
        )
        db.add(submission)
        await db.flush()

        # 5. Load or create default test cases
        test_cases = question.test_cases
        if not test_cases:
            # Fallback test case if none seeded yet
            default_tc = QuestionTestCase(
                question_id=question.id,
                input_data="[2, 7, 11, 15]\n9",
                expected_output="[0, 1]",
                is_hidden=False,
                weight=1.0,
            )
            db.add(default_tc)
            await db.flush()
            test_cases = [default_tc]

        # 6. Execute Test Cases via Judge0
        passed_count = 0
        total_time_ms = 0.0
        max_memory_kb = 0.0
        results: list[TestResult] = []

        for tc in test_cases:
            res = await judge0_client.execute_test_case(
                source_code=payload.source_code,
                stdin=tc.input_data,
                expected_output=tc.expected_output,
                language_id=payload.language_id,
            )

            is_pass = res.status == TestResultStatus.PASSED
            if is_pass:
                passed_count += 1

            if res.execution_time_ms:
                total_time_ms += res.execution_time_ms
            if res.memory_kb and res.memory_kb > max_memory_kb:
                max_memory_kb = res.memory_kb

            test_result = TestResult(
                submission_id=submission.id,
                test_case_id=tc.id,
                status=res.status,
                actual_output=res.actual_output,
                execution_time_ms=res.execution_time_ms,
                memory_kb=res.memory_kb,
                error_category=res.error_message,
            )
            db.add(test_result)
            results.append(test_result)

        # 7. Update Submission Final Stats
        total_count = len(test_cases)
        submission.passed_tests = passed_count
        submission.total_tests = total_count
        submission.runtime_ms = round(total_time_ms, 2) if total_time_ms > 0 else None
        submission.memory_kb = round(max_memory_kb, 2) if max_memory_kb > 0 else None
        submission.execution_status = (
            ExecutionStatus.COMPLETED
            if any(r.status == TestResultStatus.PASSED for r in results) or passed_count == total_count
            else ExecutionStatus.FAILED
        )

        # 8. Add a Turn to the Interview dialogue summarizing the submission
        turn_query = await db.execute(
            select(InterviewTurn)
            .where(InterviewTurn.session_id == session_id)
            .order_by(InterviewTurn.sequence_number.desc())
        )
        last_turn = turn_query.scalars().first()
        next_seq = (last_turn.sequence_number + 1) if last_turn else 1

        cand_turn = InterviewTurn(
            session_id=session_id,
            sequence_number=next_seq,
            speaker=TurnSpeaker.CANDIDATE,
            question_id=question.id,
            content=f"Submitted code solution ({passed_count}/{total_count} tests passed).\n\n```python\n{payload.source_code}\n```",
            turn_metadata={"submission_id": str(submission.id), "passed": passed_count, "total": total_count},
        )
        db.add(cand_turn)

        feedback_content = (
            f"All {total_count} test cases passed! Outstanding work on the solution logic and execution efficiency."
            if passed_count == total_count
            else f"Your solution passed {passed_count} of {total_count} test cases. Review edge cases and potential runtime/logical discrepancies in the test results."
        )

        ai_turn = InterviewTurn(
            session_id=session_id,
            sequence_number=next_seq + 1,
            speaker=TurnSpeaker.ASSISTANT,
            question_id=question.id,
            content=feedback_content,
            turn_metadata={"submission_id": str(submission.id)},
        )
        db.add(ai_turn)

        await db.commit()
        await db.refresh(submission)
        return submission

    async def get_submission(
        self,
        db: AsyncSession,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CodingSubmission:
        res = await db.execute(
            select(CodingSubmission)
            .options(selectinload(CodingSubmission.test_results))
            .where(CodingSubmission.id == submission_id)
        )
        sub = res.scalar_one_or_none()
        if not sub:
            raise NotFoundError("Coding submission not found.")
        if sub.user_id != user_id:
            raise ForbiddenError("You do not have access to this submission.")
        return sub

    async def get_candidate_safe_results(
        self,
        db: AsyncSession,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[TestResultPublic]:
        """Retrieves test results with hidden test inputs and expected outputs strictly redacted."""
        sub = await self.get_submission(db, submission_id, user_id)

        # Query results with test case metadata
        res = await db.execute(
            select(TestResult, QuestionTestCase)
            .join(QuestionTestCase, TestResult.test_case_id == QuestionTestCase.id)
            .where(TestResult.submission_id == sub.id)
            .order_by(QuestionTestCase.created_at)
        )
        pairs = res.all()

        safe_results: list[TestResultPublic] = []
        for test_result, test_case in pairs:
            if test_case.is_hidden:
                # Redact sensitive input and outputs
                safe_results.append(
                    TestResultPublic(
                        id=test_result.id,
                        test_case_id=test_result.test_case_id,
                        status=test_result.status,
                        is_hidden=True,
                        input_data=None,
                        expected_output=None,
                        actual_output=None,
                        execution_time_ms=test_result.execution_time_ms,
                        memory_kb=test_result.memory_kb,
                        error_category=None if test_result.status == TestResultStatus.PASSED else "Hidden test failed",
                        created_at=test_result.created_at,
                    )
                )
            else:
                safe_results.append(
                    TestResultPublic(
                        id=test_result.id,
                        test_case_id=test_result.test_case_id,
                        status=test_result.status,
                        is_hidden=False,
                        input_data=test_case.input_data,
                        expected_output=test_case.expected_output,
                        actual_output=test_result.actual_output,
                        execution_time_ms=test_result.execution_time_ms,
                        memory_kb=test_result.memory_kb,
                        error_category=test_result.error_category,
                        created_at=test_result.created_at,
                    )
                )

        return safe_results


coding_service = CodingService()
