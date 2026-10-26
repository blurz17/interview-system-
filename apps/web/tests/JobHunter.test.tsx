import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "../src/features/auth/AuthContext";
import { JobHunterPage } from "../src/features/job_hunter/JobHunterPage";

describe("JobHunterPage Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Job Hunter page title, tabs, and input fields", async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/resumes")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <JobHunterPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText("Job Hunter & Match Engine")).toBeInTheDocument();
    expect(screen.getByText("Input Parameters")).toBeInTheDocument();
    expect(screen.getByText("No Analysis Executed Yet")).toBeInTheDocument();
    expect(screen.getByText("Analyze Fit & Generate Strategy")).toBeInTheDocument();
  });

  it("successfully renders analysis scorecard and requirements matrix when analysis completes", async () => {
    const mockAnalysisResult = {
      overall_match_score: 85,
      verdict: "Strong Match",
      job_meta: {
        title: "Senior Backend Engineer",
        company: "TechCorp",
        location: "Remote / EU",
        url: "https://example.com/jobs/123",
      },
      candidate_location: "Egypt",
      location_eligible: true,
      location_notes: "Eligible for contract.",
      timezone_eligible: true,
      timezone_notes: "Timezone aligns well.",
      hard_requirements_analysis: [
        {
          id: "req1",
          requirement: "Python & FastAPI Experience",
          status: "Passed",
          weight: "20 pts",
          cv_evidence: "Extensive FastAPI projects built.",
          matches: ["python", "fastapi"],
        },
      ],
      bonus_points_analysis: [
        {
          skill: "Docker & Cloud",
          matched: true,
          notes: "Docker is listed in CV.",
        },
      ],
      key_strengths: ["Strong API design"],
      critical_gaps: ["No major gaps"],
      tailored_cv_bullets_to_add: [
        "Architected asynchronous FastAPI endpoints with sub-100ms latency.",
      ],
      recruiter_outreach_message: "Hi Recruiter, I am excited about the role...",
      engine_used: "CareerPilot AI Engine",
    };

    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/resumes")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        });
      }
      if (url.includes("/api/v1/job-hunter/analyze")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockAnalysisResult),
        });
      }
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <JobHunterPage />
        </BrowserRouter>
      </AuthProvider>
    );

    // Switch to paste text and submit
    const pasteTab = screen.getByText("Paste Text");
    fireEvent.click(pasteTab);

    const cvTextarea = screen.getByPlaceholderText(/Paste candidate resume/i);
    fireEvent.change(cvTextarea, { target: { value: "Backend Developer with Python and FastAPI." } });

    const submitBtn = screen.getByText("Analyze Fit & Generate Strategy");
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("85%")).toBeInTheDocument();
      expect(screen.getByText("Senior Backend Engineer")).toBeInTheDocument();
      expect(screen.getByText("Python & FastAPI Experience")).toBeInTheDocument();
      expect(screen.getByText("Copy Pitch")).toBeInTheDocument();
    });
  });
});
