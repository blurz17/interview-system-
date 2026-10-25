import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { VoiceInputControls } from "../src/features/voice/components/VoiceInputControls";

describe("VoiceInputControls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders recording button and read aloud controls", () => {
    const handleTranscript = vi.fn();

    render(
      <VoiceInputControls
        onTranscriptReady={handleTranscript}
        latestAssistantMessage="Explain database indexing."
      />
    );

    expect(screen.getByText("Record Spoken Answer")).toBeInTheDocument();
    expect(screen.getByText("Read Aloud")).toBeInTheDocument();
  });

  it("handles microphone permission failure gracefully with text fallback", async () => {
    const handleTranscript = vi.fn();

    // Mock getUserMedia rejection
    Object.defineProperty(navigator, "mediaDevices", {
      value: {
        getUserMedia: vi.fn().mockRejectedValue(new Error("Permission denied")),
      },
      writable: true,
    });

    render(
      <VoiceInputControls
        onTranscriptReady={handleTranscript}
      />
    );

    const recordBtn = screen.getByText("Record Spoken Answer");
    fireEvent.click(recordBtn);

    const alert = await screen.findByText(/Microphone access denied or unavailable/i);
    expect(alert).toBeInTheDocument();
  });
});
