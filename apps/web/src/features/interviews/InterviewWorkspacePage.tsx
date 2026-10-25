import React, { useEffect, useState, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  Send,
  Bot,
  User,
  AlertCircle,
  CheckCircle,
  XCircle,
  ArrowLeft,
  Award,
  Sparkles,
  Code2,
  MessageSquare,
} from "lucide-react";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import {
  getInterviewSession,
  submitInterviewTurn,
  completeInterviewSession,
  abandonInterviewSession,
} from "./api/interviews-api";
import { submitCode, getSubmissionResults } from "../coding/api/coding-api";
import { CodingSubmissionPublic, TestResultPublic } from "../coding/types";
import { CodeEditor } from "../coding/components/CodeEditor";
import { TestResultsPanel } from "../coding/components/TestResultsPanel";
import { InterviewSession, InterviewTurn } from "./types";
import { ApiError } from "../../lib/api-client";

export const InterviewWorkspacePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [session, setSession] = useState<InterviewSession | null>(null);
  const [turns, setTurns] = useState<InterviewTurn[]>([]);
  const [candidateInput, setCandidateInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Coding environment state
  const [sourceCode, setSourceCode] = useState<string>(
    "def two_sum(nums: list[int], target: int) -> list[int]:\n    # Implement solution here\n    seen = {}\n    for i, num in enumerate(nums):\n        diff = target - num\n        if diff in seen:\n            return [seen[diff], i]\n        seen[num] = i\n    return []\n"
  );
  const [codingSubmission, setCodingSubmission] = useState<CodingSubmissionPublic | null>(null);
  const [testResults, setTestResults] = useState<TestResultPublic[]>([]);
  const [isExecutingCode, setIsExecutingCode] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    if (!id) return;

    setIsLoading(true);
    getInterviewSession(id)
      .then((data) => {
        setSession(data);
        setTurns(data.turns || []);
        setIsLoading(false);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setErrorMessage(err.message);
        } else {
          setErrorMessage("Failed to load interview session.");
        }
        setIsLoading(false);
      });
  }, [id]);

  useEffect(() => {
    scrollToBottom();
  }, [turns]);

  const handleSubmitResponse = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!id || !candidateInput.trim() || isSubmitting) return;

    const text = candidateInput.trim();
    setCandidateInput("");
    setIsSubmitting(true);
    setErrorMessage(null);

    // Optimistically add candidate turn to UI
    const optimisticTurn: InterviewTurn = {
      id: `temp-${Date.now()}`,
      sequence_number: turns.length + 1,
      speaker: "candidate",
      content: text,
      input_mode: "text",
      created_at: new Date().toISOString(),
    };
    setTurns((prev) => [...prev, optimisticTurn]);

    try {
      const assistantTurn = await submitInterviewTurn(id, text);
      // Append assistant's answer / next question
      setTurns((prev) => [...prev, assistantTurn]);

      // If the response indicates completion or final question
      if (assistantTurn.turn_metadata?.is_final) {
        // Refresh session status
        const updated = await getInterviewSession(id);
        setSession(updated);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to submit response. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunAndSubmitCode = async () => {
    if (!id || isExecutingCode || !sourceCode.trim()) return;

    // Find active question id from latest assistant turn
    const activeQuestionTurn = turns
      .slice()
      .reverse()
      .find((t) => t.speaker === "assistant" && t.question_id);
    const questionId = activeQuestionTurn?.question_id;

    if (!questionId) {
      setErrorMessage("No active coding question found in current session.");
      return;
    }

    setIsExecutingCode(true);
    setErrorMessage(null);

    try {
      const sub = await submitCode(id, {
        question_id: questionId,
        source_code: sourceCode,
        language_id: 71,
      });
      setCodingSubmission(sub);

      const results = await getSubmissionResults(sub.id);
      setTestResults(results);

      // Refresh interview session to display newly recorded turns in conversation
      const refreshedSession = await getInterviewSession(id);
      setSession(refreshedSession);
      setTurns(refreshedSession.turns || []);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to execute code in sandbox.");
      }
    } finally {
      setIsExecutingCode(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmitResponse();
    }
  };

  const handleCompleteEarly = async () => {
    if (!id) return;
    const confirm = window.confirm(
      "Are you sure you want to conclude this interview session now? Your evaluation report will be compiled."
    );
    if (!confirm) return;

    try {
      setIsSubmitting(true);
      const updated = await completeInterviewSession(id);
      setSession(updated);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to complete interview.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAbandon = async () => {
    if (!id) return;
    const confirm = window.confirm(
      "Are you sure you want to abandon this interview session? Progress will be marked abandoned."
    );
    if (!confirm) return;

    try {
      setIsSubmitting(true);
      const updated = await abandonInterviewSession(id);
      setSession(updated);
      navigate("/dashboard");
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to abandon session.");
      }
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent" />
        <p className="mt-4 text-slate-600">Loading interview workspace...</p>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-800 mt-3">Interview Not Found</h2>
        <p className="text-slate-600 mt-1">{errorMessage || "Could not load session."}</p>
        <Link to="/dashboard" className="mt-4 inline-block">
          <Button variant="outline">Return to Dashboard</Button>
        </Link>
      </div>
    );
  }

  const isCompleted = session.status === "completed";
  const isAbandoned = session.status === "abandoned";
  const isInProgress = session.status === "in_progress" || session.status === "created";
  const isCoding = session.interview_type === "coding";

  // Calculate question count
  const questionTurns = turns.filter(
    (t) => t.speaker === "assistant" && t.turn_metadata?.question_number
  );
  const currentQuestionNumber =
    questionTurns.length > 0
      ? questionTurns[questionTurns.length - 1].turn_metadata?.question_number || questionTurns.length
      : 1;

  return (
    <div className={`mx-auto px-4 py-6 space-y-6 ${isCoding ? "max-w-7xl" : "max-w-5xl"}`}>
      {/* Top Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
            <Link to="/dashboard" className="flex items-center gap-1 hover:text-slate-800 transition-colors">
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Dashboard</span>
            </Link>
            <span>/</span>
            <span>Interview Session</span>
          </div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-slate-900">{session.target_role}</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-blue-100 text-blue-800 flex items-center gap-1">
              {isCoding ? <Code2 className="h-3.5 w-3.5" /> : <MessageSquare className="h-3.5 w-3.5" />}
              {session.interview_type}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-medium capitalize bg-slate-100 text-slate-700">
              {session.difficulty}
            </span>
            {isCompleted && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 flex items-center gap-1">
                <CheckCircle className="h-3 w-3" /> Completed
              </span>
            )}
            {isAbandoned && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 flex items-center gap-1">
                <XCircle className="h-3 w-3" /> Abandoned
              </span>
            )}
          </div>
        </div>

        {isInProgress && (
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCompleteEarly}
              disabled={isSubmitting || isExecutingCode}
            >
              Finish Early
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleAbandon}
              disabled={isSubmitting || isExecutingCode}
            >
              Abandon
            </Button>
          </div>
        )}
      </div>

      {/* Error notification */}
      {errorMessage && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {isCompleted && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-emerald-100 text-emerald-700 rounded-lg">
              <Award className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-emerald-950">
                Interview Completed Successfully!
              </h3>
              <p className="text-sm text-emerald-800">
                All scheduled questions have been evaluated. Check your performance report and skill mastery metrics.
              </p>
            </div>
          </div>
          <Link to={`/interviews/${id}/report`}>
            <Button variant="primary" className="whitespace-nowrap">
              View Evaluation Report
            </Button>
          </Link>
        </div>
      )}

      {/* Main Workspace Layout (Split for coding, single column for technical) */}
      <div className={`grid gap-6 ${isCoding ? "grid-cols-1 lg:grid-cols-12" : "grid-cols-1"}`}>
        {/* Left Column: Conversational Dialogue & Explanation */}
        <div className={`space-y-4 ${isCoding ? "lg:col-span-5" : ""}`}>
          <Card className="p-0 overflow-hidden border-slate-200 shadow-sm flex flex-col min-h-[480px] max-h-[620px]">
            {/* Header bar of conversation card */}
            <div className="bg-slate-50 border-b border-slate-200 px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
                <Bot className="h-4 w-4 text-blue-600" />
                <span>AI Interview Dialogue</span>
              </div>
              <div className="text-xs text-slate-500 font-medium">
                Active Question: <span className="font-semibold text-slate-800">#{currentQuestionNumber}</span>
              </div>
            </div>

            {/* Scrollable messages container */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              {turns.length === 0 ? (
                <div className="py-12 text-center text-slate-400">
                  <Sparkles className="h-8 w-8 mx-auto mb-2 text-blue-400 animate-pulse" />
                  <p>The interviewer is initializing your questions...</p>
                </div>
              ) : (
                turns.map((turn, idx) => {
                  const isAssistant = turn.speaker === "assistant";
                  return (
                    <div
                      key={turn.id || idx}
                      className={`flex gap-3 ${isAssistant ? "justify-start" : "justify-end"}`}
                    >
                      {isAssistant && (
                        <div className="h-8 w-8 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                          <Bot className="h-4 w-4" />
                        </div>
                      )}

                      <div
                        className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed shadow-sm ${
                          isAssistant
                            ? "bg-slate-50 text-slate-900 border border-slate-200"
                            : "bg-blue-600 text-white"
                        }`}
                      >
                        <div
                          className={`text-xs font-semibold mb-1 flex items-center justify-between gap-3 ${
                            isAssistant ? "text-slate-500" : "text-blue-200"
                          }`}
                        >
                          <span>
                            {isAssistant
                              ? turn.turn_metadata?.question_number
                                ? `Interviewer • Question #${turn.turn_metadata.question_number}`
                                : "Interviewer"
                              : "You"}
                          </span>
                          <span>
                            {new Date(turn.created_at).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </span>
                        </div>

                        <div className="whitespace-pre-wrap">{turn.content}</div>
                      </div>

                      {!isAssistant && (
                        <div className="h-8 w-8 rounded-full bg-slate-700 text-white flex items-center justify-center shrink-0 shadow-sm">
                          <User className="h-4 w-4" />
                        </div>
                      )}
                    </div>
                  );
                })
              )}

              {isSubmitting && (
                <div className="flex gap-3 justify-start">
                  <div className="h-8 w-8 rounded-full bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm text-slate-500 flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-blue-600 animate-ping" />
                    <span>Interviewer is analyzing your response...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </Card>

          {/* Quick Chat Input in Dialogue */}
          {isInProgress && (
            <form onSubmit={handleSubmitResponse} className="space-y-3">
              <div className="relative border border-slate-300 rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 bg-white shadow-sm">
                <textarea
                  value={candidateInput}
                  onChange={(e) => setCandidateInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isSubmitting}
                  placeholder={
                    isCoding
                      ? "Ask interviewer for a hint, clarify requirements, or explain approach... (Ctrl+Enter to send)"
                      : "Type your technical explanation, architecture breakdown, or code approach... (Press Ctrl+Enter to submit)"
                  }
                  className="w-full h-24 p-3 text-sm text-slate-900 focus:outline-none resize-none placeholder:text-slate-400"
                />
                <div className="bg-slate-50 border-t border-slate-200 px-3 py-2 flex items-center justify-between">
                  <div className="text-[11px] text-slate-500">
                    <kbd className="px-1 py-0.5 bg-slate-200 text-slate-700 rounded border border-slate-300 font-mono text-[10px]">
                      Ctrl
                    </kbd>{" "}
                    +{" "}
                    <kbd className="px-1 py-0.5 bg-slate-200 text-slate-700 rounded border border-slate-300 font-mono text-[10px]">
                      Enter
                    </kbd>
                  </div>
                  <Button
                    type="submit"
                    variant="primary"
                    size="sm"
                    disabled={!candidateInput.trim() || isSubmitting}
                    isLoading={isSubmitting}
                    className="flex items-center gap-1.5 text-xs py-1 px-3"
                  >
                    <span>Send</span>
                    <Send className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Right Column: Monaco Code Editor & Live Test Results (in coding mode) */}
        {isCoding && (
          <div className="lg:col-span-7 flex flex-col gap-4">
            <div className="h-[420px]">
              <CodeEditor
                value={sourceCode}
                onChange={setSourceCode}
                onSubmit={handleRunAndSubmitCode}
                isSubmitting={isExecutingCode}
                language="python"
                readOnly={!isInProgress}
              />
            </div>

            <div>
              <TestResultsPanel
                submission={codingSubmission}
                results={testResults}
                isLoading={isExecutingCode}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
