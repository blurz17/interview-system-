import asyncio

from app.db.session import async_session_maker
from app.modules.questions.seed import seed_questions


async def main():
    async with async_session_maker() as session:
        await seed_questions(session)
        print("Question bank successfully seeded into database.")


if __name__ == "__main__":
    asyncio.run(main())
