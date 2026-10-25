import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { HoneVoiceInterviewView } from "../src/features/voice/components/HoneVoiceInterviewView";
import { InterviewSession, InterviewTurn } from "../src/features/interviews/types";

describe("HoneVoiceInterviewView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockSession: InterviewSession = {
    id: "sess-123",
    target_role: "Software Engineer (Backend)",
    interview_type: "system_design",
    interaction_mode: "voice",
    difficulty: "intermediate",
    status: "in_progress",
    created_at: new Date().toISOString(),
  };

  const mockTurns: InterviewTurn[] = [
    {
      id: "turn-1",
      sequence_number: 1,
      speaker: "assistant",
      content: "Hello and welcome! In a distributed microservices setup, how do you prevent cascading failures?",
      input_mode: "voice",
      turn_metadata: { question_number: 1, is_final: false },
      created_at: new Date().toISOString(),
    },
  ];

  it("renders Hone voice interface with brand, title, connected status badge, and End interview button", () => {
    const handleTurnSubmitted = vi.fn().mockResolvedValue(undefined);
    const handleEndInterview = vi.fn().mockResolvedValue(undefined);
    const handleLeaveInterview = vi.fn();

    render(
      <HoneVoiceInterviewView
        session={mockSession}
        turns={mockTurns}
        onTurnSubmitted={handleTurnSubmitted}
        onEndInterview={handleEndInterview}
        onLeaveInterview={handleLeaveInterview}
        isSubmitting={false}
        errorMessage={null}
      />
    );

    expect(screen.getByText("Hone")).toBeInTheDocument();
    expect(screen.getByText("Back to practice")).toBeInTheDocument();
    expect(screen.getByText("Software Engineer (Backend) interview")).toBeInTheDocument();
    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("End interview")).toBeInTheDocument();
    expect(screen.getByText("Join Voice Call")).toBeInTheDocument();
  });

  it("triggers onEndInterview when clicking the coral End interview button", () => {
    const handleTurnSubmitted = vi.fn().mockResolvedValue(undefined);
    const handleEndInterview = vi.fn().mockResolvedValue(undefined);
    const handleLeaveInterview = vi.fn();

    render(
      <HoneVoiceInterviewView
        session={mockSession}
        turns={mockTurns}
        onTurnSubmitted={handleTurnSubmitted}
        onEndInterview={handleEndInterview}
        onLeaveInterview={handleLeaveInterview}
        isSubmitting={false}
        errorMessage={null}
      />
    );

    const endBtn = screen.getByText("End interview");
    fireEvent.click(endBtn);
    expect(handleEndInterview).toHaveBeenCalledTimes(1);
  });

  it("opens and closes transcript drawer when clicking transcript button", () => {
    const handleTurnSubmitted = vi.fn().mockResolvedValue(undefined);
    const handleEndInterview = vi.fn().mockResolvedValue(undefined);
    const handleLeaveInterview = vi.fn();

    render(
      <HoneVoiceInterviewView
        session={mockSession}
        turns={mockTurns}
        onTurnSubmitted={handleTurnSubmitted}
        onEndInterview={handleEndInterview}
        onLeaveInterview={handleLeaveInterview}
        isSubmitting={false}
        errorMessage={null}
      />
    );

    const viewTranscriptBtn = screen.getByText("View transcript history");
    fireEvent.click(viewTranscriptBtn);

    expect(screen.getByText("Conversation Transcript")).toBeInTheDocument();
    expect(screen.getByText(/how do you prevent cascading failures/i)).toBeInTheDocument();

    const closeBtn = screen.getByText("✕ Close");
    fireEvent.click(closeBtn);

    expect(screen.queryByText("Conversation Transcript")).not.toBeInTheDocument();
  });
});
