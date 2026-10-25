import React, { useState, useRef, useEffect } from "react";
import { Mic, Square, Volume2, VolumeX, AlertCircle, Sparkles, Check } from "lucide-react";
import { Button } from "../../../components/ui/Button";
import { transcribeAudio } from "../api/voice-api";

interface VoiceInputControlsProps {
  onTranscriptReady: (text: string) => void;
  disabled?: boolean;
  latestAssistantMessage?: string;
}

export const VoiceInputControls: React.FC<VoiceInputControlsProps> = ({
  onTranscriptReady,
  disabled = false,
  latestAssistantMessage,
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptPreview, setTranscriptPreview] = useState<string>("");
  const [isTtsActive, setIsTtsActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    };
  }, []);

  const startRecording = async () => {
    setErrorMessage(null);
    setTranscriptPreview("");
    audioChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setIsTranscribing(true);

        try {
          const res = await transcribeAudio(audioBlob);
          setTranscriptPreview(res.text);
        } catch {
          setErrorMessage("Failed to transcribe audio. You can use typed input directly.");
        } finally {
          setIsTranscribing(false);
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);
      setRecordingSeconds(0);

      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch {
      setErrorMessage("Microphone access denied or unavailable. Fallback to typed input.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const handleSpeakAssistantMessage = () => {
    if (!latestAssistantMessage || !window.speechSynthesis) return;

    if (isTtsActive) {
      window.speechSynthesis.cancel();
      setIsTtsActive(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(latestAssistantMessage);
    utterance.rate = 1.0;
    utterance.onend = () => setIsTtsActive(false);
    utterance.onerror = () => setIsTtsActive(false);

    setIsTtsActive(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleApplyTranscript = () => {
    if (transcriptPreview.trim()) {
      onTranscriptReady(transcriptPreview.trim());
      setTranscriptPreview("");
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-3">
      {errorMessage && (
        <div className="p-2.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Voice Controls Bar */}
      <div className="flex items-center justify-between bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs">
        <div className="flex items-center gap-2">
          {!isRecording ? (
            <button
              type="button"
              onClick={startRecording}
              disabled={disabled || isTranscribing}
              className="p-1.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white transition-colors flex items-center gap-1.5 px-3"
            >
              <Mic className="h-3.5 w-3.5" />
              <span className="font-medium text-[11px]">Record Spoken Answer</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={stopRecording}
              className="p-1.5 rounded-full bg-red-600 hover:bg-red-700 text-white transition-colors flex items-center gap-1.5 px-3 animate-pulse"
            >
              <Square className="h-3.5 w-3.5" />
              <span className="font-medium text-[11px]">Stop Recording ({formatTime(recordingSeconds)})</span>
            </button>
          )}

          {isTranscribing && (
            <span className="text-slate-500 flex items-center gap-1 text-[11px]">
              <Sparkles className="h-3 w-3 text-blue-500 animate-spin" />
              Transcribing audio via Whisper...
            </span>
          )}
        </div>

        {/* Read Aloud Button */}
        {latestAssistantMessage && typeof window !== "undefined" && "speechSynthesis" in window && (
          <button
            type="button"
            onClick={handleSpeakAssistantMessage}
            title={isTtsActive ? "Stop speech playback" : "Read interviewer question aloud"}
            className="flex items-center gap-1 text-slate-600 hover:text-slate-900 px-2 py-1 rounded hover:bg-slate-200/60 transition-colors"
          >
            {isTtsActive ? (
              <>
                <VolumeX className="h-3.5 w-3.5 text-blue-600" />
                <span className="text-[11px] font-medium text-blue-600">Stop Voice</span>
              </>
            ) : (
              <>
                <Volume2 className="h-3.5 w-3.5" />
                <span className="text-[11px] font-medium">Read Aloud</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Transcript Preview & Correction (Per Section 8.2) */}
      {transcriptPreview && (
        <div className="bg-blue-50/50 border border-blue-200 rounded-lg p-3 text-xs space-y-2">
          <div className="flex items-center justify-between text-blue-900 font-semibold">
            <span>Voice Transcript Preview (Review or edit before inserting):</span>
            <button
              type="button"
              onClick={() => setTranscriptPreview("")}
              className="text-slate-400 hover:text-slate-600"
            >
              Cancel
            </button>
          </div>
          <textarea
            value={transcriptPreview}
            onChange={(e) => setTranscriptPreview(e.target.value)}
            className="w-full h-16 p-2 bg-white border border-blue-200 rounded text-xs text-slate-800 focus:outline-none"
          />
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={handleApplyTranscript}
              className="flex items-center gap-1 text-xs py-1 px-3"
            >
              <Check className="h-3 w-3" />
              <span>Use Transcript</span>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
