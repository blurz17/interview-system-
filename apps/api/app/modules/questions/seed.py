from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import QuestionTestCase
from app.models.profile import ExperienceLevel
from app.models.question import Question, QuestionType
from app.models.skill import Skill

SEED_QUESTIONS = [
    {
        "title": "Two Sum (Target Pair Finder)",
        "prompt": (
            "Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.\n\n"
            "Assume exactly one valid answer exists. Return indices in 0-indexed format.\n\n"
            "```python\n"
            "def two_sum(nums: list[int], target: int) -> list[int]:\n"
            "    # O(N) hash map solution expected\n"
            "    pass\n"
            "```"
        ),
        "question_type": QuestionType.CODING,
        "difficulty": ExperienceLevel.BEGINNER,
        "category": "algorithms",
        "skill_slug": "data-structures-algorithms",
        "starter_code": "def two_sum(nums: list[int], target: int) -> list[int]:\n    seen = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in seen:\n            return [seen[diff], i]\n        seen[num] = i\n    return []\n",
        "expected_answer_criteria": [
            {"criterion": "Correctness across all test cases", "weight": 0.5},
            {"criterion": "O(N) time complexity using hash map lookup", "weight": 0.3},
            {"criterion": "Handling duplicates and negative integers", "weight": 0.2},
        ],
        "solution_explanation": "Using a dictionary to store previously seen numbers and their indices allows checking for the complement in O(1) average time, resulting in an overall O(N) time and O(N) space complexity.",
        "test_cases": [
            {"input_data": "[2, 7, 11, 15]\n9", "expected_output": "[0, 1]", "is_hidden": False, "weight": 1.0},
            {"input_data": "[3, 2, 4]\n6", "expected_output": "[1, 2]", "is_hidden": False, "weight": 1.0},
            {"input_data": "[3, 3]\n6", "expected_output": "[0, 1]", "is_hidden": True, "weight": 1.5},
            {"input_data": "[-1, -2, -3, -4, -5]\n-8", "expected_output": "[2, 4]", "is_hidden": True, "weight": 1.5},
        ],
    },
    {
        "title": "Valid Parentheses",
        "prompt": (
            "Given a string `s` containing only the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.\n\n"
            "An input string is valid if open brackets are closed by the same type of brackets and in the correct order.\n\n"
            "```python\n"
            "def is_valid(s: str) -> bool:\n"
            "    # Stack-based matching\n"
            "    pass\n"
            "```"
        ),
        "question_type": QuestionType.CODING,
        "difficulty": ExperienceLevel.BEGINNER,
        "category": "algorithms",
        "skill_slug": "data-structures-algorithms",
        "starter_code": "def is_valid(s: str) -> bool:\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return not stack\n",
        "expected_answer_criteria": [
            {"criterion": "Uses stack to match bracket ordering", "weight": 0.5},
            {"criterion": "O(N) time and O(N) space complexity", "weight": 0.3},
            {"criterion": "Properly handles unmatched closing brackets", "weight": 0.2},
        ],
        "solution_explanation": "A stack allows last-in-first-out pairing. When an opening bracket is seen, push it. When a closing bracket appears, check if the top of the stack matches its corresponding open bracket.",
        "test_cases": [
            {"input_data": "()", "expected_output": "True", "is_hidden": False, "weight": 1.0},
            {"input_data": "()[]{}", "expected_output": "True", "is_hidden": False, "weight": 1.0},
            {"input_data": "(]", "expected_output": "False", "is_hidden": True, "weight": 1.0},
            {"input_data": "([)]", "expected_output": "False", "is_hidden": True, "weight": 1.0},
            {"input_data": "{[]}", "expected_output": "True", "is_hidden": True, "weight": 1.5},
        ],
    },
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
            skill_id = skill_map.get(q_data.get("skill_slug"))
            question = Question(
                title=q_data["title"],
                prompt=q_data["prompt"],
                question_type=q_data["question_type"],
                difficulty=q_data["difficulty"],
                category=q_data["category"],
                skill_id=skill_id,
                starter_code=q_data.get("starter_code"),
                expected_answer_criteria=q_data["expected_answer_criteria"],
                solution_explanation=q_data.get("solution_explanation"),
                is_active=True,
            )
            db.add(question)
            await db.flush()

            # Add test cases if defined
            for tc in q_data.get("test_cases", []):
                test_case = QuestionTestCase(
                    question_id=question.id,
                    input_data=tc["input_data"],
                    expected_output=tc["expected_output"],
                    is_hidden=tc.get("is_hidden", False),
                    weight=tc.get("weight", 1.0),
                )
                db.add(test_case)

    await db.commit()
