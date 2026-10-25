import React, { useEffect, useState, useRef, useCallback } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Play,
  RotateCcw,
} from "lucide-react";
import { InterviewSession, InterviewTurn } from "../../interviews/types";

interface HoneVoiceInterviewViewProps {
  session: InterviewSession;
  turns: InterviewTurn[];
  onTurnSubmitted: (text: string) => Promise<void>;
  onEndInterview: () => Promise<void>;
  onLeaveInterview: () => void;
  isSubmitting: boolean;
  errorMessage: string | null;
}

export const HoneVoiceInterviewView: React.FC<HoneVoiceInterviewViewProps> = ({
  session,
  turns,
  onTurnSubmitted,
  onEndInterview,
  onLeaveInterview,
  isSubmitting,
  errorMessage,
}) => {
  // Voice states: 'idle' | 'ai_speaking' | 'listening' | 'processing'
  const [callState, setCallState] = useState<"idle" | "ai_speaking" | "listening" | "processing">("idle");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [hasUserStartedAudio, setHasUserStartedAudio] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [liveCandidateTranscript, setLiveCandidateTranscript] = useState("");
  const [showTranscriptDrawer, setShowTranscriptDrawer] = useState(false);
  const [typedFallbackInput, setTypedFallbackInput] = useState("");
  const [showTypedInput, setShowTypedInput] = useState(false);

  // References
  const recognitionRef = useRef<any>(null);
  const speechSilenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const elapsedTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSpokenAssistantTurnIdRef = useRef<string | null>(null);
  const candidateTranscriptRef = useRef<string>("");

  // Latest assistant message
  const assistantTurns = turns.filter((t) => t.speaker === "assistant");
  const latestAssistantTurn = assistantTurns.length > 0 ? assistantTurns[assistantTurns.length - 1] : null;

  // Format timer as mm:ss (or m:ss as shown in screenshot "0:05")
  const formatTimer = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
  };

  // Timer ticker
  useEffect(() => {
    if (hasUserStartedAudio) {
      elapsedTimerRef.current = setInterval(() => {
        setElapsedSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    };
  }, [hasUserStartedAudio]);

  // Clean up speech on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      if (speechSilenceTimerRef.current) {
        clearTimeout(speechSilenceTimerRef.current);
      }
    };
  }, []);

  // Helper: Speak text via SpeechSynthesis
  const speakAssistantText = useCallback(
    (text: string) => {
      if (!soundEnabled || typeof window === "undefined" || !window.speechSynthesis) {
        // Fallback directly to listening if audio disabled
        setCallState("listening");
        startListening();
        return;
      }

      window.speechSynthesis.cancel();
      // Remove markdown formatting for cleaner speech synthesis
      const cleanText = text
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/#{1,6}\s?/g, "")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .trim();

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      // Select a natural English voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferredVoice =
        voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Neural"))) ||
        voices.find((v) => v.lang.startsWith("en"));
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      setCallState("ai_speaking");

      utterance.onend = () => {
        // Once AI finishes speaking, switch to listening to candidate
        setCallState("listening");
        startListening();
      };

      utterance.onerror = (e) => {
        console.warn("Speech synthesis error:", e);
        setCallState("listening");
        startListening();
      };

      window.speechSynthesis.speak(utterance);
    },
    [soundEnabled]
  );

  // Trigger speech when a new assistant turn arrives
  useEffect(() => {
    if (!hasUserStartedAudio || !latestAssistantTurn) return;

    if (latestAssistantTurn.id !== lastSpokenAssistantTurnIdRef.current) {
      lastSpokenAssistantTurnIdRef.current = latestAssistantTurn.id;
      speakAssistantText(latestAssistantTurn.content);
    }
  }, [hasUserStartedAudio, latestAssistantTurn, speakAssistantText]);

  // Submit candidate answer
  const submitCandidateSpeech = useCallback(
    async (textToSend: string) => {
      const trimmed = textToSend.trim();
      if (!trimmed || isSubmitting) return;

      // Stop speech recognition
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }

      setCallState("processing");
      setLiveCandidateTranscript("");
      candidateTranscriptRef.current = "";

      try {
        await onTurnSubmitted(trimmed);
      } catch (err) {
        console.error("Turn submission error:", err);
        setCallState("listening");
      }
    },
    [isSubmitting, onTurnSubmitted]
  );

  // Start speech recognition for candidate speech
  const startListening = useCallback(() => {
    if (isMuted) return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("SpeechRecognition API not supported in this browser. Fallback to typed input.");
      return;
    }

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setCallState("listening");
      };

      recognition.onresult = (event: any) => {
        let interim = "";
        let final = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript + " ";
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        const fullCurrentTranscript = (candidateTranscriptRef.current + " " + final + interim).trim();
        setLiveCandidateTranscript(fullCurrentTranscript);

        if (final) {
          candidateTranscriptRef.current = (candidateTranscriptRef.current + " " + final).trim();
        }

        // Voice Activity Detection (VAD) silence timer:
        // If user has spoken something and then is silent for 2.2 seconds, automatically submit!
        if (speechSilenceTimerRef.current) {
          clearTimeout(speechSilenceTimerRef.current);
        }

        if (fullCurrentTranscript.length > 5) {
          speechSilenceTimerRef.current = setTimeout(() => {
            if (candidateTranscriptRef.current.trim().length > 3) {
              submitCandidateSpeech(candidateTranscriptRef.current.trim());
            }
          }, 2200);
        }
      };

      recognition.onerror = (event: any) => {
        if (event.error !== "no-speech") {
          console.warn("Recognition error:", event.error);
        }
      };

      recognition.onend = () => {
        // If still in listening state and not muted, automatically restart
        if (callState === "listening" && !isMuted) {
          try {
            recognition.start();
          } catch {}
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.error("Failed to initialize speech recognition:", e);
    }
  }, [callState, isMuted, submitCandidateSpeech]);

  // Initial Join / Start Call click (unlocks browser speech audio)
  const handleStartCall = () => {
    setHasUserStartedAudio(true);
    if (latestAssistantTurn) {
      lastSpokenAssistantTurnIdRef.current = latestAssistantTurn.id;
      speakAssistantText(latestAssistantTurn.content);
    } else {
      setCallState("listening");
      startListening();
    }
  };

  // Toggle Mute
  const handleToggleMute = () => {
    if (!isMuted) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsMuted(true);
    } else {
      setIsMuted(false);
      if (callState === "listening") {
        startListening();
      }
    }
  };

  // Toggle Sound Output
  const handleToggleSound = () => {
    if (soundEnabled) {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setSoundEnabled(false);
    } else {
      setSoundEnabled(true);
      if (callState === "ai_speaking" && latestAssistantTurn) {
        speakAssistantText(latestAssistantTurn.content);
      }
    }
  };

  // Skip AI Speech
  const handleSkipSpeech = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setCallState("listening");
    startListening();
  };

  // Repeat AI Speech
  const handleRepeatSpeech = () => {
    if (latestAssistantTurn) {
      speakAssistantText(latestAssistantTurn.content);
    }
  };

  // Finish candidate speaking early
  const handleDoneSpeaking = () => {
    if (speechSilenceTimerRef.current) {
      clearTimeout(speechSilenceTimerRef.current);
    }
    const textToSend = candidateTranscriptRef.current.trim() || liveCandidateTranscript.trim();
    if (textToSend) {
      submitCandidateSpeech(textToSend);
    }
  };

  // Handle manual typed fallback submit
  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!typedFallbackInput.trim()) return;
    submitCandidateSpeech(typedFallbackInput);
    setTypedFallbackInput("");
    setShowTypedInput(false);
  };

  // Determine status pill badge and colors
  let statusBadge = (
    <span className="px-3.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5 shadow-sm">
      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
      Connected
    </span>
  );

  if (isSubmitting || callState === "processing") {
    statusBadge = (
      <span className="px-3.5 py-1 rounded-full text-xs font-semibold bg-blue-500/15 text-blue-300 border border-blue-500/30 flex items-center gap-1.5 shadow-sm animate-pulse">
        <Sparkles className="h-3 w-3 text-blue-400 animate-spin" />
        AI Thinking...
      </span>
    );
  } else if (callState === "ai_speaking") {
    statusBadge = (
      <span className="px-3.5 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/40 flex items-center gap-1.5 shadow-[0_0_15px_rgba(168,85,247,0.3)]">
        <span className="flex gap-0.5 items-end h-3">
          <span className="w-0.5 h-2 bg-purple-400 rounded animate-pulse" />
          <span className="w-0.5 h-3 bg-purple-300 rounded animate-pulse delay-75" />
          <span className="w-0.5 h-1.5 bg-purple-400 rounded animate-pulse delay-150" />
        </span>
        AI Speaking...
      </span>
    );
  } else if (callState === "listening") {
    statusBadge = (
      <span className="px-3.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5 shadow-[0_0_15px_rgba(16,185,129,0.25)]">
        <Mic className="h-3 w-3 text-emerald-400 animate-bounce" />
        Listening...
      </span>
    );
  }

  // Active question number
  const questionNumber =
    latestAssistantTurn?.turn_metadata?.question_number ||
    turns.filter((t) => t.speaker === "assistant").length ||
    1;

  return (
    <div className="fixed inset-0 z-50 min-h-screen w-full bg-[#090a10] text-slate-100 flex flex-col justify-between select-none overflow-x-hidden font-sans">
      {/* Background ambient radial gradients */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[580px] h-[580px] bg-purple-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[340px] h-[340px] bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Top Header matching Hone screenshot */}
      <header className="relative z-10 w-full pt-8 pb-4 flex flex-col items-center gap-2">
        {/* Brand Dot + Name */}
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#8b5cf6] shadow-[0_0_10px_#8b5cf6]" />
          <span className="text-sm font-semibold tracking-wide text-white">Hone</span>
        </div>

        {/* Back link */}
        <button
          onClick={onLeaveInterview}
          className="text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1 mt-0.5 group"
        >
          <span className="group-hover:-translate-x-0.5 transition-transform">←</span>
          <span>Back to practice</span>
        </button>

        {/* Title */}
        <h1 className="text-2xl md:text-3xl font-semibold text-white tracking-tight mt-3 text-center px-4">
          {session.target_role} interview
        </h1>
      </header>

      {/* Center Voice Orb Experience */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-4 py-6">
        {/* Outer Circular Ring with Status on top and Timer on bottom */}
        <div className="relative flex items-center justify-center">
          {/* Subtle Outer Boundary Ring */}
          <div className="w-72 h-72 md:w-80 md:h-80 rounded-full border border-purple-500/15 relative flex items-center justify-center">
            {/* Top Badge positioned on ring border */}
            <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 bg-[#090a10] px-2">
              {statusBadge}
            </div>

            {/* Pulsing Orb */}
            {!hasUserStartedAudio ? (
              // Initial Start Call Orb
              <button
                onClick={handleStartCall}
                className="group relative w-44 h-44 md:w-52 md:h-52 rounded-full bg-gradient-to-tr from-[#6d28d9] via-[#8b5cf6] to-[#a855f7] shadow-[0_0_60px_rgba(139,92,246,0.5)] hover:shadow-[0_0_90px_rgba(168,85,247,0.75)] hover:scale-105 active:scale-95 transition-all duration-300 flex flex-col items-center justify-center cursor-pointer text-white"
              >
                <Play className="h-10 w-10 text-white fill-white translate-x-0.5 mb-1 group-hover:scale-110 transition-transform" />
                <span className="text-xs font-semibold uppercase tracking-wider text-purple-100">
                  Join Voice Call
                </span>
              </button>
            ) : (
              // Live Interactive Orb
              <div
                onClick={callState === "listening" ? handleDoneSpeaking : handleRepeatSpeech}
                title={callState === "listening" ? "Click when done speaking" : "Click to repeat question"}
                className={`relative w-44 h-44 md:w-52 md:h-52 rounded-full cursor-pointer transition-all duration-500 flex items-center justify-center ${
                  callState === "ai_speaking"
                    ? "bg-gradient-to-tr from-[#6d28d9] via-[#8b5cf6] to-[#c084fc] shadow-[0_0_90px_rgba(168,85,247,0.7)] animate-pulse scale-105"
                    : callState === "listening"
                    ? "bg-gradient-to-tr from-[#4c1d95] via-[#7c3aed] to-[#8b5cf6] shadow-[0_0_80px_rgba(124,58,237,0.6)] hover:scale-105"
                    : callState === "processing"
                    ? "bg-gradient-to-tr from-[#312e81] via-[#4f46e5] to-[#7c3aed] shadow-[0_0_70px_rgba(99,102,241,0.5)] animate-spin-slow"
                    : "bg-gradient-to-tr from-[#581c87] via-[#7c3aed] to-[#9333ea] shadow-[0_0_50px_rgba(139,92,246,0.4)]"
                }`}
              >
                {/* Subtle core ring */}
                <div className="w-28 h-28 rounded-full bg-white/10 blur-sm pointer-events-none" />

                {/* Status indicator icon at center */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-white/90">
                  {callState === "ai_speaking" && (
                    <Volume2 className="h-8 w-8 text-white/80 animate-pulse" />
                  )}
                  {callState === "listening" && (
                    <Mic className="h-8 w-8 text-white/90 animate-bounce" />
                  )}
                  {callState === "processing" && (
                    <Sparkles className="h-8 w-8 text-blue-200 animate-spin" />
                  )}
                </div>
              </div>
            )}

            {/* Bottom Timer on ring border */}
            <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-[#090a10] px-3 text-xs md:text-sm font-mono text-slate-300 font-medium">
              {formatTimer(elapsedSeconds)}
            </div>
          </div>
        </div>

        {/* Live Subtitles & Transcriptions */}
        <div className="mt-8 max-w-xl w-full text-center px-4 min-h-[90px] flex flex-col items-center justify-center">
          {!hasUserStartedAudio ? (
            <p className="text-sm text-slate-400 max-w-sm">
              Tap the purple orb to connect your microphone and begin your real-time voice interview.
            </p>
          ) : callState === "ai_speaking" && latestAssistantTurn ? (
            <div className="space-y-1.5 animate-fade-in">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-purple-400">
                Interviewer • Question #{questionNumber}
              </span>
              <p className="text-sm md:text-base text-slate-200 font-medium leading-relaxed max-h-24 overflow-y-auto px-2">
                "{latestAssistantTurn.content}"
              </p>
            </div>
          ) : callState === "listening" ? (
            <div className="space-y-1.5 animate-fade-in">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">
                Your Spoken Response
              </span>
              <p className="text-sm md:text-base text-slate-300 italic min-h-[28px]">
                {liveCandidateTranscript || "Speak naturally into your microphone... pauses will auto-submit"}
              </p>
              {liveCandidateTranscript.length > 5 && (
                <button
                  onClick={handleDoneSpeaking}
                  className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 transition-colors mt-1"
                >
                  <CheckCircle2 className="h-3 w-3" />
                  <span>Done speaking? Send answer</span>
                </button>
              )}
            </div>
          ) : callState === "processing" ? (
            <div className="space-y-1">
              <p className="text-sm text-blue-300 animate-pulse">
                Evaluating response and preparing next technical question...
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Ready for next turn.</p>
          )}

          {errorMessage && (
            <div className="mt-2 text-xs text-rose-400 flex items-center justify-center gap-1.5 bg-rose-500/10 px-3 py-1.5 rounded-lg border border-rose-500/20">
              <AlertCircle className="h-3.5 w-3.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* In-Call Quick Controls */}
        {hasUserStartedAudio && (
          <div className="flex items-center gap-3 mt-4 text-slate-400">
            {/* Mic Toggle */}
            <button
              onClick={handleToggleMute}
              title={isMuted ? "Unmute microphone" : "Mute microphone"}
              className={`p-2.5 rounded-full border transition-all ${
                isMuted
                  ? "bg-rose-500/20 border-rose-500/40 text-rose-400"
                  : "bg-slate-900 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
              }`}
            >
              {isMuted ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </button>

            {/* Audio Voice Output Toggle */}
            <button
              onClick={handleToggleSound}
              title={soundEnabled ? "Mute AI voice output" : "Enable AI voice output"}
              className={`p-2.5 rounded-full border transition-all ${
                !soundEnabled
                  ? "bg-rose-500/20 border-rose-500/40 text-rose-400"
                  : "bg-slate-900 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
              }`}
            >
              {soundEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            </button>

            {/* Replay or Skip Voice Button */}
            {callState === "ai_speaking" ? (
              <button
                onClick={handleSkipSpeech}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white transition-all"
              >
                Skip voice
              </button>
            ) : (
              <button
                onClick={handleRepeatSpeech}
                title="Repeat interviewer question"
                className="p-2.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-all"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            )}

            {/* Manual Keyboard Fallback */}
            <button
              onClick={() => setShowTypedInput((prev) => !prev)}
              title="Type response manually"
              className={`p-2.5 rounded-full border transition-all ${
                showTypedInput
                  ? "bg-purple-500/20 border-purple-500/40 text-purple-300"
                  : "bg-slate-900 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
              }`}
            >
              <MessageSquare className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Typed Fallback Input Drawer */}
        {showTypedInput && (
          <form
            onSubmit={handleManualSubmit}
            className="w-full max-w-lg mt-4 bg-slate-900/90 border border-slate-800 p-3 rounded-xl shadow-xl space-y-2 animate-fade-in"
          >
            <textarea
              value={typedFallbackInput}
              onChange={(e) => setTypedFallbackInput(e.target.value)}
              placeholder="Prefer typing? Type your engineering thoughts here and press send..."
              rows={2}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowTypedInput(false)}
                className="text-xs px-3 py-1 text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!typedFallbackInput.trim() || isSubmitting}
                className="text-xs px-4 py-1.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg font-medium transition-colors"
              >
                Send Answer
              </button>
            </div>
          </form>
        )}
      </main>

      {/* Bottom Action Footer with Coral End Interview Button */}
      <footer className="relative z-10 w-full pb-10 pt-4 flex flex-col items-center justify-center gap-3">
        <button
          onClick={onEndInterview}
          disabled={isSubmitting}
          className="bg-[#ff5a60] hover:bg-[#e0484e] active:scale-95 text-white font-medium text-sm md:text-base px-8 py-3 rounded-full shadow-lg shadow-rose-950/40 transition-all duration-150 cursor-pointer disabled:opacity-50"
        >
          End interview
        </button>

        {/* View transcript button */}
        <button
          onClick={() => setShowTranscriptDrawer((prev) => !prev)}
          className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
        >
          {showTranscriptDrawer ? "Hide transcript" : "View transcript history"}
        </button>
      </footer>

      {/* Transcript History Drawer Modal */}
      {showTranscriptDrawer && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 flex flex-col h-full animate-slide-left">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="font-semibold text-white text-base">Conversation Transcript</h3>
              <button
                onClick={() => setShowTranscriptDrawer(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕ Close
              </button>
            </div>
            <div className="flex-1 overflow-y-auto py-4 space-y-4">
              {turns.map((turn, idx) => (
                <div
                  key={turn.id || idx}
                  className={`p-3 rounded-xl text-xs space-y-1 ${
                    turn.speaker === "assistant"
                      ? "bg-purple-950/30 border border-purple-900/30 text-purple-200"
                      : "bg-slate-800/60 border border-slate-700/40 text-slate-200 ml-4"
                  }`}
                >
                  <div className="font-semibold text-[10px] uppercase tracking-wider text-slate-400">
                    {turn.speaker === "assistant" ? "Interviewer" : "You"}
                  </div>
                  <div className="whitespace-pre-wrap leading-relaxed">{turn.content}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
