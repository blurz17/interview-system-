from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import ExperienceLevel
from app.models.skill import Skill, SkillPrerequisite

SEED_SKILLS: list[tuple[str, str, str, str, ExperienceLevel]] = [
    (
        "python",
        "Python",
        "languages",
        "Core Python, idioms, data structures, and standard library",
        ExperienceLevel.BEGINNER,
    ),
    (
        "javascript",
        "JavaScript",
        "languages",
        "Modern ECMAScript, event loop, closures, and async programming",
        ExperienceLevel.BEGINNER,
    ),
    (
        "typescript",
        "TypeScript",
        "languages",
        "Static typing, generics, utility types, and interfaces",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "sql",
        "SQL",
        "databases",
        "Relational querying, joins, aggregations, and subqueries",
        ExperienceLevel.BEGINNER,
    ),
    (
        "go",
        "Go",
        "languages",
        "Go syntax, goroutines, channels, and standard tooling",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "java",
        "Java",
        "languages",
        "Object-oriented design, JVM internals, memory management, and streams",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "arrays-strings",
        "Arrays and Strings",
        "data_structures",
        "Contiguous memory, two-pointer techniques, and sliding window",
        ExperienceLevel.BEGINNER,
    ),
    (
        "hash-tables",
        "Hash Tables",
        "data_structures",
        "Hash functions, collision resolution, hash maps, and frequency maps",
        ExperienceLevel.BEGINNER,
    ),
    (
        "linked-lists",
        "Linked Lists",
        "data_structures",
        "Singly/doubly linked lists, traversal, cycle detection, and reversal",
        ExperienceLevel.BEGINNER,
    ),
    (
        "trees-bst",
        "Trees and Binary Search Trees",
        "data_structures",
        "Tree traversals, binary search trees, and balance properties",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "heaps-priority-queues",
        "Heaps and Priority Queues",
        "data_structures",
        "Min-heaps, max-heaps, top-k elements, and priority queues",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "graphs",
        "Graphs",
        "data_structures",
        "Adjacency matrices, adjacency lists, and graph representations",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "sorting-searching",
        "Sorting and Searching",
        "algorithms",
        "Binary search, merge sort, quicksort, and time complexities",
        ExperienceLevel.BEGINNER,
    ),
    (
        "recursion-backtracking",
        "Recursion and Backtracking",
        "algorithms",
        "Recursive thinking, base cases, state exploration, and pruning",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "graph-traversal",
        "Graph Traversal (BFS & DFS)",
        "algorithms",
        "Breadth-first search, depth-first search, and shortest paths",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "dynamic-programming",
        "Dynamic Programming",
        "algorithms",
        "Overlapping subproblems, optimal substructure, memoization, and tabulation",
        ExperienceLevel.ADVANCED,
    ),
    (
        "indexing-optimization",
        "Indexing and Query Optimization",
        "databases",
        "B-Trees, composite indexes, query plans, and EXPLAIN analysis",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "acid-transactions",
        "ACID and Transactions",
        "databases",
        "Atomicity, consistency, isolation levels, and concurrency anomalies",
        ExperienceLevel.ADVANCED,
    ),
    (
        "rest-apis",
        "RESTful API Design",
        "system_design",
        "HTTP verbs, status codes, statelessness, and idempotency",
        ExperienceLevel.BEGINNER,
    ),
    (
        "caching-redis",
        "Caching and Redis",
        "system_design",
        "Cache invalidation, write-through, write-back, and eviction policies",
        ExperienceLevel.INTERMEDIATE,
    ),
    (
        "microservices",
        "Microservices Architecture",
        "system_design",
        "Service decomposition, inter-service communication, and resilience",
        ExperienceLevel.ADVANCED,
    ),
    (
        "message-queues",
        "Message Queues",
        "system_design",
        "Asynchronous messaging, pub/sub, delivery guarantees, and backpressure",
        ExperienceLevel.ADVANCED,
    ),
]

SEED_PREREQUISITES: list[tuple[str, str]] = [
    ("trees-bst", "recursion-backtracking"),
    ("trees-bst", "linked-lists"),
    ("heaps-priority-queues", "arrays-strings"),
    ("graphs", "arrays-strings"),
    ("graph-traversal", "graphs"),
    ("graph-traversal", "recursion-backtracking"),
    ("dynamic-programming", "recursion-backtracking"),
    ("indexing-optimization", "sql"),
    ("acid-transactions", "sql"),
    ("caching-redis", "rest-apis"),
    ("microservices", "rest-apis"),
    ("message-queues", "rest-apis"),
]


async def seed_skills(db: AsyncSession) -> None:
    existing_skills = (await db.execute(select(Skill.slug))).scalars().all()
    existing_set = set(existing_skills)

    for slug, name, category, desc, diff in SEED_SKILLS:
        if slug not in existing_set:
            skill = Skill(
                slug=slug,
                name=name,
                category=category,
                description=desc,
                difficulty_level=diff,
                is_active=True,
            )
            db.add(skill)

    await db.flush()

    all_skills = (await db.execute(select(Skill))).scalars().all()
    skill_map = {s.slug: s for s in all_skills}

    for skill_slug, prereq_slug in SEED_PREREQUISITES:
        if skill_slug in skill_map and prereq_slug in skill_map:
            skill_id = skill_map[skill_slug].id
            prereq_id = skill_map[prereq_slug].id

            exists_prereq = await db.execute(
                select(SkillPrerequisite).where(
                    SkillPrerequisite.skill_id == skill_id,
                    SkillPrerequisite.prerequisite_skill_id == prereq_id,
                )
            )
            if not exists_prereq.scalar_one_or_none():
                db.add(SkillPrerequisite(skill_id=skill_id, prerequisite_skill_id=prereq_id))

    await db.commit()
