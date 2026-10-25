from dataclasses import dataclass
from typing import Any

DEFAULT_RUBRIC_VERSION = "v1.0"


@dataclass(frozen=True)
class RubricCriterion:
    key: str
    name: str
    weight: float
    description: str


RUBRIC_V1_0: dict[str, Any] = {
    "version": DEFAULT_RUBRIC_VERSION,
    "title": "CareerPilot Standard Technical & Coding Rubric",
    "description": (
        "Evaluates candidates based on verified test-case executions, conceptual depth, "
        "algorithmic complexity, and trade-off articulation."
    ),
    "dimensions": [
        RubricCriterion(
            key="code_correctness",
            name="Code Execution & Test Correctness",
            weight=0.40,
            description="Proportion of verified unit test cases passed in isolated sandbox.",
        ),
        RubricCriterion(
            key="conceptual_depth",
            name="Conceptual Depth & Technical Precision",
            weight=0.30,
            description="Accuracy, core terminology, and domain depth demonstrated in verbal/text responses.",
        ),
        RubricCriterion(
            key="edge_cases_complexity",
            name="Complexity Analysis & Edge Cases",
            weight=0.20,
            description="Consideration of asymptotic time/space bounds and boundary condition handling.",
        ),
        RubricCriterion(
            key="communication_clarity",
            name="Structure & Coherence",
            weight=0.10,
            description="Ability to organize solutions coherently and explain technical decisions clearly.",
        ),
    ],
}
