import asyncio

from app.db.session import async_session_maker
from app.modules.skills.seed import seed_skills


async def main():
    async with async_session_maker() as session:
        await seed_skills(session)
        print("Skill catalog successfully seeded into database.")


if __name__ == "__main__":
    asyncio.run(main())
