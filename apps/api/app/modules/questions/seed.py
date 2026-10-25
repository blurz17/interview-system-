from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import ExperienceLevel
from app.models.question import Question, QuestionType
from app.models.skill import Skill

SEED_QUESTIONS = [
    {
        "title": "Database Indexing & B-Trees",
        "prompt": "Explain how a B-Tree index improves query performance in relational databases. Under what conditions could adding an index actually degrade database performance?",
        "question_type": QuestionType.TECHNICAL,
        "difficulty": ExperienceLevel.INTERMEDIATE,
        "category": "databases",
        "skill_slug": "indexing-optimization",
        "expected_answer_criteria": [
            {"criterion": "B-Tree structure & O(log N) lookup", "weight": 0.4},
            {"criterion": "Impact on INSERT/UPDATE/DELETE write overhead", "weight": 0.3},
            {"criterion": "Storage footprint & index selectivity", "weight": 0.3},
        ],
        "solution_explanation": "B-Tree indexes provide logarithmic search times for equality and range queries by maintaining a balanced search tree. However, every INSERT, UPDATE on indexed columns, and DELETE requires updating the index tree, which introduces write amplification and disk I/O.",
    },
    {
        "title": "ACID Transactions & Isolation Levels",
        "prompt": "What are the four ACID properties in database transactions? Can you compare 'Read Committed' vs 'Serializable' isolation levels and mention which concurrency anomalies can still occur under Read Committed?",
        "question_type": QuestionType.TECHNICAL,
        "difficulty": ExperienceLevel.ADVANCED,
        "category": "databases",
        "skill_slug": "acid-transactions",
        "expected_answer_criteria": [
            {"criterion": "Defines Atomicity, Consistency, Isolation, Durability", "weight": 0.3},
            {"criterion": "Explains Read Committed vs Serializable", "weight": 0.4},
            {"criterion": "Identifies Non-repeatable reads and Phantom reads", "weight": 0.3},
        ],
        "solution_explanation": "In Read Committed, transactions only see committed data, preventing dirty reads. However, non-repeatable reads (a row read twice changes) and phantom reads (new rows matching a query appear) can occur. Serializable prevents all anomalies via strict two-phase locking or SSI.",
    },
    {
        "title": "Python GIL and Concurrency",
        "prompt": "What is the Global Interpreter Lock (GIL) in CPython, and how does it influence the execution of CPU-bound tasks versus I/O-bound tasks in a multithreaded application?",
        "question_type": QuestionType.TECHNICAL,
        "difficulty": ExperienceLevel.INTERMEDIATE,
        "category": "languages",
        "skill_slug": "python",
        "expected_answer_criteria": [
            {"criterion": "Explains GIL mutex protecting Python memory management", "weight": 0.4},
            {"criterion": "Explains CPU-bound limitation (single core bottleneck)", "weight": 0.3},
            {
                "criterion": "Explains I/O-bound release of GIL (async or threading effectiveness)",
                "weight": 0.3,
            },
        ],
        "solution_explanation": "The GIL is a mutex in CPython that ensures only one thread executes Python bytecode at once. For CPU-bound tasks, threading does not achieve multi-core parallelism (multiprocessing is required). For I/O-bound tasks, the GIL is released during network/file operations, allowing threads to wait concurrently.",
    },
    {
        "title": "REST API Idempotency",
        "prompt": "What does idempotency mean in the context of HTTP and RESTful APIs? Which HTTP methods are naturally idempotent, and how would you implement an idempotent payment endpoint using POST?",
        "question_type": QuestionType.TECHNICAL,
        "difficulty": ExperienceLevel.INTERMEDIATE,
        "category": "system_design",
        "skill_slug": "rest-apis",
        "expected_answer_criteria": [
            {
                "criterion": "Definition of idempotency (same outcome on repeated calls)",
                "weight": 0.3,
            },
            {
                "criterion": "Identifies GET, PUT, DELETE as idempotent; POST as non-idempotent",
                "weight": 0.3,
            },
            {"criterion": "Idempotency-Key header pattern with cache/database lock", "weight": 0.4},
        ],
        "solution_explanation": "An operation is idempotent if executing it multiple times yields the same system state as a single execution. GET, PUT, and DELETE are idempotent. For POST payments, client sends a unique Idempotency-Key header; the server checks if that key has already been processed and returns the cached result without double charging.",
    },
    {
        "title": "Caching Strategies & Invalidation",
        "prompt": "Compare Cache-Aside (Lazy Loading) with Write-Through caching. What are the trade-offs of each, and how would you handle cache invalidation when data in the primary database is updated?",
        "question_type": QuestionType.TECHNICAL,
        "difficulty": ExperienceLevel.INTERMEDIATE,
        "category": "system_design",
        "skill_slug": "caching-redis",
        "expected_answer_criteria": [
            {"criterion": "Contrasts Cache-Aside and Write-Through workflows", "weight": 0.4},
            {"criterion": "Discusses cache miss penalty vs write latency overhead", "weight": 0.3},
            {
                "criterion": "Invalidation techniques: TTL, explicit key deletion, pub/sub invalidation",
                "weight": 0.3,
            },
        ],
        "solution_explanation": "Cache-Aside loads entries on demand upon cache misses; primary DB is written first, then cache key is invalidated or deleted. Write-Through updates cache and database synchronously, guaranteeing cache freshness at the cost of higher write latency.",
    },
    {
        "title": "Dynamic Programming Identification",
        "prompt": "How do you systematically determine whether an algorithmic problem is suitable for Dynamic Programming rather than simple recursion or a greedy approach?",
        "question_type": QuestionType.TECHNICAL,
        "difficulty": ExperienceLevel.ADVANCED,
        "category": "algorithms",
        "skill_slug": "dynamic-programming",
        "expected_answer_criteria": [
            {"criterion": "Optimal Substructure property", "weight": 0.4},
            {"criterion": "Overlapping Subproblems property", "weight": 0.4},
            {
                "criterion": "Comparison against Greedy local choice vs global optimum",
                "weight": 0.2,
            },
        ],
        "solution_explanation": "DP requires both Optimal Substructure (an optimal solution to the problem contains optimal solutions to its subproblems) and Overlapping Subproblems (the same subproblems are computed repeatedly). If subproblems do not overlap, divide-and-conquer is used; if local optimal choices always lead to global optimum without backtracking, greedy applies.",
    },
]


async def seed_questions(db: AsyncSession) -> None:
    # Load all skills map
    skills = (await db.execute(select(Skill))).scalars().all()
    skill_map = {s.slug: s.id for s in skills}

    existing_titles = (await db.execute(select(Question.title))).scalars().all()
    existing_set = set(existing_titles)

    for q_data in SEED_QUESTIONS:
        if q_data["title"] not in existing_set:
            skill_id = skill_map.get(q_data["skill_slug"])
            question = Question(
                title=q_data["title"],
                prompt=q_data["prompt"],
                question_type=q_data["question_type"],
                difficulty=q_data["difficulty"],
                category=q_data["category"],
                skill_id=skill_id,
                expected_answer_criteria=q_data["expected_answer_criteria"],
                solution_explanation=q_data.get("solution_explanation"),
                is_active=True,
            )
            db.add(question)

    await db.commit()
