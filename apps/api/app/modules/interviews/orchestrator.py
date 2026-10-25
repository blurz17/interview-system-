import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError
from app.db.base import utc_now
from app.integrations.llm.provider import HuggingFaceLLMProvider
from app.models.interview import (
    InteractionMode,
    InterviewSession,
    InterviewStatus,
    InterviewTurn,
    TurnSpeaker,
)
from app.models.question import Question
from app.models.resume_skill import ResumeSkill

TARGET_QUESTIONS_PER_SESSION = 3


class InterviewOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = HuggingFaceLLMProvider()

    async def get_session_by_id(self, session_id: uuid.UUID) -> InterviewSession | None:
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(selectinload(InterviewSession.turns).selectinload(InterviewTurn.question))
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def start_session(self, session: InterviewSession) -> InterviewTurn:
        if session.status != InterviewStatus.CREATED:
            raise BadRequestError(f"Cannot start interview in '{session.status}' status.")

        # Transition state machine: created -> in_progress
        session.status = InterviewStatus.IN_PROGRESS
        session.started_at = utc_now()

        # Select first question matching target role or difficulty
        question = await self._select_next_question(session, asked_question_ids=[])
        if not question:
            raise BadRequestError("No active questions available for this interview type.")

        # Create Turn 1 (Assistant)
        greeting = (
            f"Hello and welcome to your technical interview for the {session.target_role} role. "
            f"We will explore core engineering concepts and practical trade-offs. "
            f"Take your time to structure your response.\n\n"
            f"**Question 1:** {question.prompt}"
        )

        turn = InterviewTurn(
            session_id=session.id,
            sequence_number=1,
            speaker=TurnSpeaker.ASSISTANT,
            question_id=question.id,
            content=greeting,
            input_mode=session.interaction_mode,
            turn_metadata={"question_number": 1, "is_final": False},
        )
        self.db.add(turn)
        await self.db.commit()
        await self.db.refresh(turn)
        return turn

    async def process_candidate_turn(
        self,
        session: InterviewSession,
        candidate_content: str,
        input_mode: InteractionMode,
    ) -> InterviewTurn:
        if session.status != InterviewStatus.IN_PROGRESS:
            raise BadRequestError(
                f"Cannot submit answers to an interview in '{session.status}' status."
            )

        # 1. Record candidate turn
        next_seq = len(session.turns) + 1
        last_turn = session.turns[-1] if session.turns else None
        current_question_id = last_turn.question_id if last_turn else None

        candidate_turn = InterviewTurn(
            session_id=session.id,
            sequence_number=next_seq,
            speaker=TurnSpeaker.CANDIDATE,
            question_id=current_question_id,
            content=candidate_content.strip(),
            input_mode=input_mode,
        )
        self.db.add(candidate_turn)
        await self.db.flush()

        # 2. Determine questions asked so far
        asked_ids = [t.question_id for t in session.turns if t.question_id is not None]
        unique_questions_count = len(set(asked_ids))

        # Check if we should conclude or present next question
        if unique_questions_count >= TARGET_QUESTIONS_PER_SESSION:
            # Concluding turn
            conclusion_text = (
                "Thank you for sharing your technical response and reasoning! "
                "That concludes our interview questions for this session. "
                "You can now click **Complete Interview** to generate your comprehensive evaluation report."
            )
            assistant_turn = InterviewTurn(
                session_id=session.id,
                sequence_number=next_seq + 1,
                speaker=TurnSpeaker.ASSISTANT,
                content=conclusion_text,
                input_mode=session.interaction_mode,
                turn_metadata={"is_final": True},
            )
        else:
            # Select next question
            next_q = await self._select_next_question(session, asked_question_ids=asked_ids)
            q_num = unique_questions_count + 1

            if next_q:
                assistant_text = (
                    f"Good explanation. Let's move on to our next topic.\n\n"
                    f"**Question {q_num}:** {next_q.prompt}"
                )
                assistant_turn = InterviewTurn(
                    session_id=session.id,
                    sequence_number=next_seq + 1,
                    speaker=TurnSpeaker.ASSISTANT,
                    question_id=next_q.id,
                    content=assistant_text,
                    input_mode=session.interaction_mode,
                    turn_metadata={"question_number": q_num, "is_final": False},
                )
            else:
                # No more questions in bank
                assistant_turn = InterviewTurn(
                    session_id=session.id,
                    sequence_number=next_seq + 1,
                    speaker=TurnSpeaker.ASSISTANT,
                    content="Thank you for your responses! That wraps up our available questions.",
                    input_mode=session.interaction_mode,
                    turn_metadata={"is_final": True},
                )

        self.db.add(assistant_turn)
        await self.db.commit()
        await self.db.refresh(assistant_turn)
        return assistant_turn

    async def complete_session(self, session: InterviewSession) -> InterviewSession:
        if session.status != InterviewStatus.IN_PROGRESS:
            raise BadRequestError(f"Cannot complete interview in '{session.status}' status.")

        session.status = InterviewStatus.COMPLETED
        session.completed_at = utc_now()
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def abandon_session(self, session: InterviewSession) -> InterviewSession:
        if session.status in (InterviewStatus.COMPLETED, InterviewStatus.ABANDONED):
            raise BadRequestError(f"Cannot abandon interview in '{session.status}' status.")

        session.status = InterviewStatus.ABANDONED
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def _select_next_question(
        self,
        session: InterviewSession,
        asked_question_ids: list[uuid.UUID],
    ) -> Question | None:
        # Priority 1: Match candidate confirmed CV skills if resume attached
        matched_question = None
        if session.resume_id:
            stmt_skills = select(ResumeSkill.skill_id).where(
                ResumeSkill.resume_id == session.resume_id
            )
            candidate_skill_ids = (await self.db.execute(stmt_skills)).scalars().all()

            if candidate_skill_ids:
                stmt_q = select(Question).where(
                    Question.skill_id.in_(candidate_skill_ids),
                    Question.id.not_in(asked_question_ids) if asked_question_ids else True,
                    Question.is_active.is_(True),
                )
                matched_question = (await self.db.execute(stmt_q)).scalars().first()

        # Priority 2: Match difficulty and category from general bank
        if not matched_question:
            stmt_diff = (
                select(Question)
                .where(
                    Question.id.not_in(asked_question_ids) if asked_question_ids else True,
                    Question.is_active.is_(True),
                )
                .order_by(Question.created_at)
            )
            matched_question = (await self.db.execute(stmt_diff)).scalars().first()

        return matched_question
