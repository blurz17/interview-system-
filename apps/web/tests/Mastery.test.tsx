import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { MasteryDashboardPage } from "../src/features/mastery/MasteryDashboardPage";
import { TrainingAssignmentPublic, UserSkillMasteryPublic } from "../src/features/mastery/types";

describe("MasteryDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders skill mastery profiles and training assignments", async () => {
    const mockMastery: UserSkillMasteryPublic[] = [
      {
        id: "m-1",
        user_id: "u-1",
        skill_id: "s-1",
        skill_name: "Python",
        skill_slug: "python",
        category: "languages",
        mastery_score: 0.85,
        confidence: 0.9,
        evidence_count: 3,
        last_assessed_at: new Date().toISOString(),
      },
    ];

    const mockAssignments: TrainingAssignmentPublic[] = [
      {
        id: "a-1",
        user_id: "u-1",
        skill_id: "s-1",
        skill_name: "Python",
        title: "Python Data Structures Drill",
        description: "Master dictionary lookup complexity and hashing.",
        exercise_type: "coding",
        difficulty: "intermediate",
        status: "pending",
        created_at: new Date().toISOString(),
      },
    ];

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/skills/mastery")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockMastery),
        });
      }
      if (url.includes("/api/v1/training/assignments")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockAssignments),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(
      <BrowserRouter>
        <MasteryDashboardPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Loading Skill Mastery graph/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Skill Mastery Engine")).toBeInTheDocument();
      expect(screen.getByText("Python Data Structures Drill")).toBeInTheDocument();
      expect(screen.getAllByText("Python").length).toBeGreaterThan(0);
      expect(screen.getAllByText(/85%/).length).toBeGreaterThan(0);
      expect(screen.getByText("Record Practice Attempt")).toBeInTheDocument();
    });

    // Click Record Practice Attempt to open the inline form
    const recordBtn = screen.getByText("Record Practice Attempt");
    fireEvent.click(recordBtn);

    expect(screen.getByText(/Simulated Score/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Submit Attempt/i })).toBeInTheDocument();
  });
});
