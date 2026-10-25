import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "../src/features/auth/AuthContext";
import { ResumeManagementPage } from "../src/features/cv/ResumeManagementPage";

describe("ResumeManagementPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders upload card and empty state when no resumes exist", async () => {
    global.fetch = vi.fn().mockImplementation((url: string) => {
      if (url.includes("/api/v1/auth/me")) {
        return Promise.resolve({ ok: false, status: 401 });
      }
      if (url.includes("/api/v1/resumes")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        });
      }
      if (url.includes("/api/v1/skills")) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.reject(new Error("Unknown URL"));
    });

    render(
      <AuthProvider>
        <BrowserRouter>
          <ResumeManagementPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText("CV Management & Skill Extraction")).toBeInTheDocument();
    expect(screen.getByText("Upload Your CV / Resume")).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText("No CV uploaded yet. Upload one above to get started.")
      ).toBeInTheDocument();
    });
  });
});
