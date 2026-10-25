import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import BadRequestError
from app.db.base import utc_now
from app.integrations.llm.provider import get_llm_provider
from app.models.interview import (
    InteractionMode,
    InterviewSession,
    InterviewStatus,
    InterviewTurn,
    InterviewType,
    TurnSpeaker,
)
from app.models.question import Question, QuestionType
from app.models.resume import Resume
from app.models.resume_skill import ResumeSkill

logger = logging.getLogger(__name__)

TARGET_QUESTIONS_PER_SESSION = 3


class InterviewOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_provider()

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

        session.status = InterviewStatus.IN_PROGRESS
        session.started_at = utc_now()

        # Handle Coding Interview mode
        if session.interview_type == InterviewType.CODING:
            question = await self._select_next_coding_question(session, asked_question_ids=[])
            if not question:
                raise BadRequestError("No active coding questions available.")

            greeting = (
                f"Hello and welcome to your coding assessment for the {session.target_role} role.\n\n"
                f"You will solve the following problem in the live code editor on the right.\n\n"
                f"### {question.title}\n\n"
                f"{question.prompt}"
            )
            turn = InterviewTurn(
                session_id=session.id,
                sequence_number=1,
                speaker=TurnSpeaker.ASSISTANT,
                question_id=question.id,
                content=greeting,
                input_mode=session.interaction_mode,
                turn_metadata={"question_number": 1, "is_final": False, "is_coding": True},
            )
            self.db.add(turn)
            await self.db.commit()
            await self.db.refresh(turn)
            return turn

        # Conversational / Live Voice Interview Mode (Hone.sh style)
        cv_context = ""
        matched_question_id = None
        if session.resume_id:
            res_resume = await self.db.execute(
                select(Resume)
                .options(selectinload(Resume.skills).selectinload(ResumeSkill.skill))
                .where(Resume.id == session.resume_id)
            )
            resume_obj = res_resume.scalar_one_or_none()
            if resume_obj:
                skills_str = ", ".join([s.skill.name for s in resume_obj.skills if s.skill])
                parsed_sample = (resume_obj.parsed_text or "")[:1500]
                cv_context = f"Candidate Confirmed Skills: {skills_str}\nResume Text Snippet:\n{parsed_sample}\n"

        is_voice = session.interaction_mode == InteractionMode.VOICE or session.interview_type in (
            "voice_mock",
            "voice_interview",
        )

        system_prompt = (
            "You are an elite, realistic technical interviewer conducting a mock interview for a software engineer. "
            "Your tone is professional, encouraging yet incisive, in the style of senior tech leads and Hone.sh. "
            f"Candidate Target Role: {session.target_role}\n"
            f"Difficulty Level: {session.difficulty}\n"
            f"Format: {'Spoken Live Voice Interview' if is_voice else 'Interactive Technical Dialogue'}\n\n"
            "Instructions:\n"
            "1. Deliver a brief, welcoming greeting (1-2 sentences) acknowledging their target role.\n"
            "2. Present Question #1: A realistic, production engineering scenario question tailored to their target role and resume background. "
            "Ask about real engineering choices (e.g. database indexing, concurrency, cache invalidation, API resiliency, distributed state, async pipelines). "
            "Do NOT ask generic textbook trivia. Avoid asking the same Global Interpreter Lock question every time. "
            f"{'Keep sentences concise, natural, and punchy for spoken audio playback.' if is_voice else ''}"
        )

        user_prompt = (
            f"Start the interview for a {session.target_role} candidate.\n"
            f"{cv_context}\n"
            "Provide the opening greeting and Question #1:"
        )

        try:
            opening_content = await self.llm.generate_text(system_prompt, user_prompt)
            if not opening_content or len(opening_content.strip()) < 20:
                opening_content = (
                    f"Hello and welcome to your technical interview for the {session.target_role} role. "
                    "We'll explore your architectural intuition and practical problem-solving skills.\n\n"
                    "**Question 1:** When designing a high-throughput backend service, how do you decide between an asynchronous event-driven architecture versus synchronous request-response, and what are the trade-offs regarding failure isolation?"
                )
        except Exception as e:
            logger.warning("Dynamic question generation failed: %s; using smart fallback", str(e))
            opening_content = (
                f"Hello and welcome to your technical interview for the {session.target_role} role.\n\n"
                "**Question 1:** In production services, database connection pool exhaustion can cause sudden latency spikes. How would you diagnose, resolve, and prevent pool starvation in an asynchronous web application?"
            )

        turn = InterviewTurn(
            session_id=session.id,
            sequence_number=1,
            speaker=TurnSpeaker.ASSISTANT,
            question_id=matched_question_id,
            content=opening_content,
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

        # Count candidate turns
        candidate_turns_count = len([t for t in session.turns if t.speaker == TurnSpeaker.CANDIDATE]) + 1
        is_voice = input_mode == InteractionMode.VOICE or session.interaction_mode == InteractionMode.VOICE

        # Determine if this should wrap up
        is_final = candidate_turns_count >= TARGET_QUESTIONS_PER_SESSION

        # Build conversation history context
        history_snippets = []
        for t in session.turns[-4:]:
            speaker_label = "Interviewer" if t.speaker == TurnSpeaker.ASSISTANT else "Candidate"
            history_snippets.append(f"{speaker_label}: {t.content[:300]}")
        history_snippets.append(f"Candidate: {candidate_content.strip()}")
        history_str = "\n".join(history_snippets)

        if is_final:
            system_prompt = (
                "You are an expert technical interviewer in a live technical mock interview. "
                "The candidate has just answered the final interview question. "
                "1. Give a warm, constructive 1-sentence reaction to their final response. "
                "2. Conclude the interview professionally, thanking them for their time and inviting them to review their detailed evaluation scorecard and performance analysis. "
                f"{'Keep it concise and natural for voice synthesis.' if is_voice else ''}"
            )
            user_prompt = f"Recent Interview Transcript:\n{history_str}\n\nConclude the interview:"
            try:
                conclusion_content = await self.llm.generate_text(system_prompt, user_prompt)
            except Exception:
                conclusion_content = (
                    "Thank you for sharing your technical thought process and reasoning! "
                    "That concludes our technical questions for this session. "
                    "You can now click **Complete Interview** to review your evaluation report and performance breakdown."
                )

            assistant_turn = InterviewTurn(
                session_id=session.id,
                sequence_number=next_seq + 1,
                speaker=TurnSpeaker.ASSISTANT,
                content=conclusion_content,
                input_mode=session.interaction_mode,
                turn_metadata={"is_final": True},
            )
        else:
            q_num = candidate_turns_count + 1
            system_prompt = (
                "You are an expert technical interviewer conducting an interview (Hone.sh style). "
                f"Candidate Target Role: {session.target_role}\n"
                f"Format: {'Live Spoken Voice Interview' if is_voice else 'Technical Q&A'}\n\n"
                "Listen closely to the candidate's latest response. "
                "Your task:\n"
                "1. In 1-2 sentences, directly acknowledge what they said (e.g. agree with a valid trade-off or note an implicit assumption they made).\n"
                "2. Push back with a sharp follow-up or challenge question: Ask about an edge case, a potential failure mode (e.g. network partition, cache invalidation, race condition, data corruption), or scale limitation of their proposal.\n"
                f"3. Frame it clearly as Question #{q_num}.\n"
                f"{'Speak naturally, concisely, and with warmth, designed for clear speech synthesis.' if is_voice else ''}"
            )
            user_prompt = (
                f"Recent Transcript:\n{history_str}\n\n"
                f"Candidate's latest answer:\n\"{candidate_content}\"\n\n"
                f"Generate your conversational follow-up / Question #{q_num}:"
            )

            try:
                follow_up_content = await self.llm.generate_text(system_prompt, user_prompt)
                if not follow_up_content or len(follow_up_content.strip()) < 15:
                    follow_up_content = (
                        f"That makes sense in terms of the baseline architecture. "
                        f"Now, let's explore resilience under stress: **Question {q_num}:** "
                        "If your downstream database replica encounters replication lag exceeding 10 seconds, how do you prevent stale reads without overwhelming the primary database?"
                    )
            except Exception as e:
                logger.warning("Dynamic follow-up generation failed: %s; using smart fallback", str(e))
                follow_up_content = (
                    f"Good reasoning on those trade-offs. Let's dig deeper: **Question {q_num}:** "
                    "How would you handle idempotent retry semantics when a client times out waiting for an order confirmation?"
                )

            assistant_turn = InterviewTurn(
                session_id=session.id,
                sequence_number=next_seq + 1,
                speaker=TurnSpeaker.ASSISTANT,
                question_id=current_question_id,
                content=follow_up_content,
                input_mode=session.interaction_mode,
                turn_metadata={"question_number": q_num, "is_final": False},
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

    async def _select_next_coding_question(
        self,
        session: InterviewSession,
        asked_question_ids: list[uuid.UUID],
    ) -> Question | None:
        stmt = (
            select(Question)
            .where(
                Question.question_type == QuestionType.CODING,
                Question.id.not_in(asked_question_ids) if asked_question_ids else True,
                Question.is_active.is_(True),
            )
            .order_by(Question.created_at)
        )
        return (await self.db.execute(stmt)).scalars().first()
