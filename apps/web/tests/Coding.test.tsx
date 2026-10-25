import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TestResultsPanel } from "../src/features/coding/components/TestResultsPanel";
import { CodingSubmissionPublic, TestResultPublic } from "../src/features/coding/types";

describe("Coding Environment Components", () => {
  it("renders test results correctly with hidden cases protected", () => {
    const mockSubmission: CodingSubmissionPublic = {
      id: "sub-100",
      session_id: "sess-100",
      question_id: "q-100",
      user_id: "u-100",
      language_id: 71,
      source_code: "def solution(): pass",
      execution_status: "completed",
      passed_tests: 1,
      total_tests: 2,
      runtime_ms: 45.2,
      memory_kb: 3120.0,
      submitted_at: new Date().toISOString(),
    };

    const mockResults: TestResultPublic[] = [
      {
        id: "tr-1",
        test_case_id: "tc-1",
        status: "passed",
        is_hidden: false,
        input_data: "[1, 2, 3]",
        expected_output: "6",
        actual_output: "6",
        execution_time_ms: 20.0,
        memory_kb: 3000.0,
        created_at: new Date().toISOString(),
      },
      {
        id: "tr-2",
        test_case_id: "tc-2",
        status: "failed",
        is_hidden: true,
        input_data: null,
        expected_output: null,
        actual_output: null,
        execution_time_ms: 25.2,
        memory_kb: 3120.0,
        error_category: "Hidden test failed",
        created_at: new Date().toISOString(),
      },
    ];

    render(<TestResultsPanel submission={mockSubmission} results={mockResults} />);

    // Check summary bar
    expect(screen.getByText("1 / 2 passed")).toBeInTheDocument();
    expect(screen.getByText("45.2 ms")).toBeInTheDocument();
    expect(screen.getByText("3120 KB")).toBeInTheDocument();

    // Case 1 is visible by default
    expect(screen.getByText("Input")).toBeInTheDocument();
    expect(screen.getByText("[1, 2, 3]")).toBeInTheDocument();
    expect(screen.getByText("Expected Output")).toBeInTheDocument();
    expect(screen.getByText("Actual Output")).toBeInTheDocument();

    // Click Case 2 (hidden)
    const case2Tab = screen.getByRole("button", { name: /Case 2/i });
    fireEvent.click(case2Tab);

    // Verify hidden case disclaimer is displayed and no input/output is leaked
    expect(screen.getByText("Hidden Evaluation Test Case")).toBeInTheDocument();
    expect(
      screen.getByText("Input data and expected output are protected for assessment integrity.")
    ).toBeInTheDocument();
  });
});
