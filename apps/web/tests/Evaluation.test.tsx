import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { EvaluationReportPage } from "../src/features/evaluations/EvaluationReportPage";
import { EvaluationReportPublic } from "../src/features/evaluations/types";

describe("EvaluationReportPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders evaluation scorecard with rubric version and traceable evidence", async () => {
    const mockReport: EvaluationReportPublic = {
      id: "report-123",
      session_id: "sess-123",
      overall_score: 87.5,
      rubric_version: "v1.0",
      summary: "Candidate demonstrated solid grasp of indexing and executed all unit test cases.",
      strengths: [
        "Passed all unit test cases for algorithm problems",
        "Clear articulation of B-Tree time complexity",
      ],
      weaknesses: [
        "Could elaborate further on database lock contention",
      ],
      recommendations: [
        "Practice distributed system trade-offs and CAP theorem scenarios",
      ],
      evaluation_status: "completed",
      skill_evidences: [
        {
          id: "ev-1",
          skill_id: "skill-1",
          skill_name: "Python",
          skill_slug: "python",
          score: 100.0,
          evidence_type: "coding_test_execution",
          explanation: "Automated sandbox verification: Passed 4 of 4 test cases.",
          confidence: 0.95,
          created_at: new Date().toISOString(),
        },
        {
          id: "ev-2",
          skill_id: "skill-2",
          skill_name: "Indexing & Optimization",
          skill_slug: "indexing-optimization",
          score: 75.0,
          evidence_type: "conceptual_turn",
          explanation: "Accurately described B-Tree lookup O(log N).",
          confidence: 0.80,
          created_at: new Date().toISOString(),
        },
      ],
      created_at: new Date().toISOString(),
    };

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/interviews/sess-123/report")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockReport),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(
      <MemoryRouter initialEntries={["/interviews/sess-123/report"]}>
        <Routes>
          <Route path="/interviews/:id/report" element={<EvaluationReportPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText(/Compiling evaluation report/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Performance Evaluation Report")).toBeInTheDocument();
      expect(screen.getByText("87.5")).toBeInTheDocument();
      expect(screen.getByText("Rubric v1.0")).toBeInTheDocument();
      expect(screen.getByText(/Candidate demonstrated solid grasp/)).toBeInTheDocument();
      expect(screen.getByText("Python")).toBeInTheDocument();
      expect(screen.getByText("Indexing & Optimization")).toBeInTheDocument();
      expect(screen.getByText("100%")).toBeInTheDocument();
    });
  });
});
