import asyncio
import logging

from app.db.session import async_session_maker
from app.modules.questions.seed import seed_questions
from app.modules.skills.seed import seed_skills

logger = logging.getLogger("careerpilot.seed")


async def seed_all() -> None:
    """Idempotently seed the entire baseline demonstration dataset."""
    async with async_session_maker() as session:
        logger.info("Seeding skills and prerequisite DAGs...")
        await seed_skills(session)
        logger.info("Seeding technical and coding question bank...")
        await seed_questions(session)
        logger.info("Database seeding complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    asyncio.run(seed_all())
