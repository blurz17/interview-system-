import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter, MemoryRouter, Routes, Route } from "react-router-dom";
import { InterviewSetupPage } from "../src/features/interviews/InterviewSetupPage";
import { InterviewWorkspacePage } from "../src/features/interviews/InterviewWorkspacePage";

describe("Interview Features", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("InterviewSetupPage", () => {
    it("renders configuration options and handles setup form", async () => {
      global.fetch = vi.fn().mockImplementation((url: string) => {
        if (url.includes("/api/v1/resumes")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve([
                {
                  id: "res-1",
                  original_filename: "resume.pdf",
                  mime_type: "application/pdf",
                  file_size_bytes: 1024,
                  parsing_status: "completed",
                  extraction_status: "completed",
                  skills: [],
                  created_at: new Date().toISOString(),
                },
              ]),
          });
        }
        return Promise.reject(new Error("Unknown URL"));
      });

      render(
        <BrowserRouter>
          <InterviewSetupPage />
        </BrowserRouter>
      );

      expect(screen.getByText("Configure Technical Interview")).toBeInTheDocument();
      expect(screen.getByText("Software Engineer (Backend)")).toBeInTheDocument();
      expect(screen.getByText("Technical Q&A")).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText(/resume\.pdf/)).toBeInTheDocument();
      });
    });
  });

  describe("InterviewWorkspacePage", () => {
    it("renders session turns and submits candidate answers", async () => {
      const mockSession = {
        id: "sess-123",
        target_role: "Software Engineer (Backend)",
        interview_type: "technical",
        interaction_mode: "text",
        difficulty: "intermediate",
        status: "in_progress",
        turns: [
          {
            id: "turn-1",
            sequence_number: 1,
            speaker: "assistant",
            content: "Explain the difference between optimistic and pessimistic concurrency control.",
            input_mode: "text",
            turn_metadata: { question_number: 1 },
            created_at: new Date().toISOString(),
          },
        ],
      };

      global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
        if (url.includes("/api/v1/interviews/sess-123/turns") && options?.method === "POST") {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                id: "turn-3",
                sequence_number: 3,
                speaker: "assistant",
                content: "Good answer. Now how does PostgreSQL implement MVCC?",
                input_mode: "text",
                turn_metadata: { question_number: 2 },
                created_at: new Date().toISOString(),
              }),
          });
        }
        if (url.includes("/api/v1/interviews/sess-123")) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve(mockSession),
          });
        }
        return Promise.reject(new Error("Unknown URL"));
      });

      render(
        <MemoryRouter initialEntries={["/interviews/sess-123"]}>
          <Routes>
            <Route path="/interviews/:id" element={<InterviewWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Explain the difference between optimistic and pessimistic concurrency control/)
        ).toBeInTheDocument();
      });

      // Find input textarea
      const textarea = screen.getByPlaceholderText(/Type your technical explanation/);
      expect(textarea).toBeInTheDocument();

      fireEvent.change(textarea, {
        target: { value: "Optimistic assumes no collision and validates at commit; pessimistic uses locks." },
      });

      const submitButton = screen.getByRole("button", { name: /Send/i });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/Good answer. Now how does PostgreSQL implement MVCC/)
        ).toBeInTheDocument();
      });
    });
  });
});
