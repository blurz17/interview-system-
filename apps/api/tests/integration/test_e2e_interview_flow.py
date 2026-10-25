import io

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import QuestionTestCase
from app.models.profile import ExperienceLevel
from app.models.question import Question, QuestionType
from app.models.skill import Skill, SkillPrerequisite


@pytest.mark.asyncio
async def test_end_to_end_candidate_journey(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Exhaustive End-to-End integration test covering the entire candidate lifecycle:

    1. Registration, Profile configuration & JWT authentication.
    2. CV upload, text parsing, and skill extraction review.
    3. Interview setup, state machine initialization (created -> in_progress).
    4. Conversational question & answer turn orchestration.
    5. Coding execution via sandboxed Judge0 engine with hidden test case protection.
    6. Interview session completion (in_progress -> completed).
    7. Evaluation report generation with v1.0 rubric, scores, and traceable evidence.
    8. Skill Mastery Engine updates with exponential moving average (alpha=0.3).
    9. Targeted training assignment generation & completion tracking.
    10. Data persistence across multiple queries.
    """
    # 0. Setup skill catalog & coding question in test DB
    skill_py = Skill(
        slug="python",
        name="Python",
        description="Core Python programming language",
        category="languages",
        difficulty_level=ExperienceLevel.BEGINNER,
        is_active=True,
    )
    skill_algo = Skill(
        slug="data-structures-algorithms",
        name="Data Structures & Algorithms",
        description="Fundamental algorithms and data structures",
        category="algorithms",
        difficulty_level=ExperienceLevel.INTERMEDIATE,
        is_active=True,
    )
    db_session.add_all([skill_py, skill_algo])
    await db_session.flush()

    # Prerequisite: Python -> Algorithms
    prereq = SkillPrerequisite(
        skill_id=skill_algo.id,
        prerequisite_skill_id=skill_py.id,
    )
    db_session.add(prereq)

    # Question with public and hidden test cases
    question = Question(
        title="Two Sum (Target Pair Finder)",
        prompt="Given an array of integers and target, return indices of two numbers that sum to target.",
        question_type=QuestionType.CODING,
        difficulty=ExperienceLevel.BEGINNER,
        category="algorithms",
        skill_id=skill_py.id,
        starter_code="def two_sum(nums, target):\n    pass\n",
        is_active=True,
    )
    db_session.add(question)
    await db_session.flush()

    tc_pub = QuestionTestCase(
        question_id=question.id,
        input_data="[2, 7, 11, 15]\n9",
        expected_output="[0, 1]",
        is_hidden=False,
        weight=1.0,
    )
    tc_hid = QuestionTestCase(
        question_id=question.id,
        input_data="[3, 3]\n6",
        expected_output="[0, 1]",
        is_hidden=True,
        weight=1.5,
    )
    db_session.add_all([tc_pub, tc_hid])
    await db_session.commit()

    # 1. Candidate Registration & Authentication
    reg_payload = {
        "email": "candidate_e2e@university.edu",
        "password": "SecurePassword123!",
        "full_name": "Alex Candidate",
        "target_role": "Backend Engineer",
        "experience_level": "intermediate",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    token = auth_data["tokens"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify profile patch
    patch_res = await client.patch(
        "/api/v1/auth/me",
        headers=auth_headers,
        json={"target_role": "Software Engineer (Backend)"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["profile"]["target_role"] == "Software Engineer (Backend)"

    # 2. CV Upload & Parsing
    cv_content = (
        b"Alex Candidate - Software Engineer\n"
        b"Skills: Python, Data Structures & Algorithms, PostgreSQL, Git\n"
        b"Experience: Built asynchronous web services and optimized database queries."
    )
    upload_res = await client.post(
        "/api/v1/resumes",
        headers=auth_headers,
        files={"file": ("alex_cv.txt", io.BytesIO(cv_content), "text/plain")},
    )
    assert upload_res.status_code == 201
    resume_data = upload_res.json()
    resume_id = resume_data["id"]
    assert resume_data["parsing_status"] == "completed"

    # Verify list of resumes
    list_res = await client.get("/api/v1/resumes", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Interview Configuration & State Machine Initialization
    create_sess_payload = {
        "target_role": "Backend Engineer",
        "interview_type": "coding",
        "difficulty": "beginner",
    }
    sess_res = await client.post(
        "/api/v1/interviews",
        headers=auth_headers,
        json=create_sess_payload,
    )
    assert sess_res.status_code == 201
    sess_data = sess_res.json()
    session_id = sess_data["id"]
    assert sess_data["status"] == "created"

    # Transition: created -> in_progress
    start_res = await client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers,
    )
    assert start_res.status_code == 200
    opening_turn = start_res.json()
    assert opening_turn["speaker"] == "assistant"
    assert len(opening_turn["content"]) > 0

    # Verify session status is now in_progress
    sess_detail = await client.get(
        f"/api/v1/interviews/{session_id}",
        headers=auth_headers,
    )
    assert sess_detail.status_code == 200
    assert sess_detail.json()["status"] == "in_progress"

    # 4. Conversational Dialogue Turn
    turn_payload = {
        "content": (
            "I would approach the Two Sum problem using a hash map to achieve O(N) time complexity "
            "and O(N) space complexity by mapping each value to its index during a single pass."
        ),
        "question_id": str(question.id),
    }
    turn_res = await client.post(
        f"/api/v1/interviews/{session_id}/turns",
        headers=auth_headers,
        json=turn_payload,
    )
    assert turn_res.status_code == 200
    ai_turn = turn_res.json()
    assert ai_turn["speaker"] == "assistant"

    # 5. Sandboxed Code Execution
    sub_payload = {
        "question_id": str(question.id),
        "language_id": 71,  # Python 3
        "source_code": (
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, num in enumerate(nums):\n"
            "        diff = target - num\n"
            "        if diff in seen:\n"
            "            return [seen[diff], i]\n"
            "        seen[num] = i\n"
            "    return []\n"
        ),
    }
    sub_res = await client.post(
        f"/api/v1/interviews/{session_id}/submissions",
        headers=auth_headers,
        json=sub_payload,
    )
    assert sub_res.status_code == 201
    sub_data = sub_res.json()
    submission_id = sub_data["id"]
    assert sub_data["execution_status"] == "completed"
    assert sub_data["passed_tests"] == sub_data["total_tests"]

    # Verify hidden test case protection (Candidate-Safe Privacy Rule)
    results_res = await client.get(
        f"/api/v1/submissions/{submission_id}/results",
        headers=auth_headers,
    )
    assert results_res.status_code == 200
    test_results = results_res.json()
    assert len(test_results) == 2
    for tr in test_results:
        if tr["is_hidden"]:
            assert tr["input_data"] is None or tr["input_data"] == ""
            assert tr["expected_output"] is None or tr["expected_output"] == ""
            assert tr["actual_output"] is None or tr["actual_output"] == ""
        else:
            assert tr["input_data"] is not None
            assert tr["expected_output"] is not None

    # 6. Complete Interview Session (in_progress -> completed)
    comp_res = await client.post(
        f"/api/v1/interviews/{session_id}/complete",
        headers=auth_headers,
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"

    # Rule check: A completed session cannot accept new interview turns
    invalid_turn = await client.post(
        f"/api/v1/interviews/{session_id}/turns",
        headers=auth_headers,
        json={"content": "Can I add one more detail?"},
    )
    assert invalid_turn.status_code in (400, 409)

    # 7. Evaluation Report Generation & Traceable Evidence
    eval_res = await client.post(
        f"/api/v1/interviews/{session_id}/evaluate",
        headers=auth_headers,
    )
    assert eval_res.status_code == 200
    report_data = eval_res.json()
    assert report_data["rubric_version"] == "v1.0"
    assert report_data["evaluation_status"] == "completed"
    assert report_data["overall_score"] > 0.0
    assert len(report_data["skill_evidences"]) >= 1

    # Verify traceable evidence record
    coding_evidence = next(
        (e for e in report_data["skill_evidences"] if e["evidence_type"] == "coding_test_execution"),
        None,
    )
    assert coding_evidence is not None
    assert f"submission:{submission_id}" == coding_evidence["evidence_reference"]
    assert coding_evidence["score"] == 100.0  # All tests passed

    # 8. Skill Mastery Engine
    mastery_res = await client.get("/api/v1/skills/mastery", headers=auth_headers)
    assert mastery_res.status_code == 200
    mastery_list = mastery_res.json()
    assert len(mastery_list) >= 1

    # Find the Python mastery record
    py_mastery = next((m for m in mastery_list if m["skill_slug"] == "python"), None)
    assert py_mastery is not None
    assert py_mastery["mastery_score"] > 0.0
    assert py_mastery["evidence_count"] >= 1

    # 9. Targeted Training Assignment Generation
    gen_res = await client.post(
        "/api/v1/training/assignments/generate",
        headers=auth_headers,
        params={"limit": 3},
    )
    assert gen_res.status_code == 200
    assignments = gen_res.json()
    assert len(assignments) >= 1
    assignment = assignments[0]
    assignment_id = assignment["id"]
    assert assignment["status"] == "pending"

    # Attempt assignment with high score
    attempt_payload = {
        "score": 95.0,
        "result_summary": "Solved all edge cases with O(N) linear time complexity.",
    }
    att_res = await client.post(
        f"/api/v1/training/assignments/{assignment_id}/attempts",
        headers=auth_headers,
        json=attempt_payload,
    )
    assert att_res.status_code == 201
    assert att_res.json()["score"] == 95.0

    # Verify assignment marked completed
    assign_detail = await client.get(
        f"/api/v1/training/assignments/{assignment_id}",
        headers=auth_headers,
    )
    assert assign_detail.status_code == 200
    assert assign_detail.json()["status"] == "completed"

    # 10. Multi-Tenant Authorization Security Check
    # Register Candidate B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "attacker_user_b@university.edu", "password": "Password123!"},
    )
    token_b = reg_b.json()["tokens"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Candidate B tries to access Candidate A's interview session
    cross_sess = await client.get(
        f"/api/v1/interviews/{session_id}",
        headers=headers_b,
    )
    assert cross_sess.status_code in (403, 404)

    # Candidate B tries to access Candidate A's evaluation report
    cross_report = await client.get(
        f"/api/v1/interviews/{session_id}/report",
        headers=headers_b,
    )
    assert cross_report.status_code in (403, 404)

    # Candidate B tries to access Candidate A's training assignment
    cross_assign = await client.get(
        f"/api/v1/training/assignments/{assignment_id}",
        headers=headers_b,
    )
    assert cross_assign.status_code in (403, 404)

    # Candidate B tries to delete Candidate A's resume
    cross_cv = await client.delete(
        f"/api/v1/resumes/{resume_id}",
        headers=headers_b,
    )
    assert cross_cv.status_code in (403, 404)
