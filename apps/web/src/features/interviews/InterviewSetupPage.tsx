import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Terminal, Sparkles, BookOpen } from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { createInterviewSession, startInterviewSession } from "./api/interviews-api";
import { getResumes } from "../cv/api/cv-api";
import { Resume } from "../cv/types";
import { InteractionMode, InterviewType } from "./types";
import { ApiError } from "../../lib/api-client";

export const InterviewSetupPage: React.FC = () => {
  const navigate = useNavigate();

  const [targetRole, setTargetRole] = useState("Software Engineer (Backend)");
  const [interviewType, setInterviewType] = useState<InterviewType>("technical");
  const [interactionMode] = useState<InteractionMode>("text");
  const [difficulty, setDifficulty] = useState<"beginner" | "intermediate" | "advanced">("intermediate");
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    getResumes().then((data) => {
      setResumes(data);
      if (data.length > 0) {
        setSelectedResumeId(data[0].id);
      }
    });
  }, []);

  const handleStart = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      // 1. Create interview session
      const session = await createInterviewSession({
        target_role: targetRole,
        interview_type: interviewType,
        interaction_mode: interactionMode,
        difficulty,
        resume_id: selectedResumeId || undefined,
      });

      // 2. Start session (transitions created -> in_progress & triggers question 1)
      await startInterviewSession(session.id);

      // 3. Navigate to workspace
      navigate(`/interviews/${session.id}`);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to start interview. Please try again.");
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Configure Technical Interview</h1>
        <p className="text-slate-600 mt-1">
          Customize your practice session. Questions will be adaptively tailored based on your target role and CV skills.
        </p>
      </div>

      {errorMessage && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
          {errorMessage}
        </div>
      )}

      <Card>
        <form onSubmit={handleStart} className="space-y-6">
          {/* Target Role */}
          <div>
            <label className="block text-sm font-semibold text-slate-800">Target Role</label>
            <select
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              className="mt-1.5 w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Software Engineer (Backend)">Software Engineer (Backend)</option>
              <option value="Software Engineer (Full Stack)">Software Engineer (Full Stack)</option>
              <option value="Frontend Engineer">Frontend Engineer</option>
              <option value="Data Engineer / Systems">Data Engineer / Systems</option>
            </select>
          </div>

          {/* Interview Type */}
          <div>
            <label className="block text-sm font-semibold text-slate-800">Interview Mode</label>
            <div className="grid grid-cols-3 gap-3 mt-1.5">
              {[
                { type: "technical", label: "Technical Q&A", icon: Terminal },
                { type: "coding", label: "Live Coding", icon: Sparkles },
                { type: "system_design", label: "System Design", icon: BookOpen },
              ].map(({ type, label, icon: Icon }) => (
                <button
                  type="button"
                  key={type}
                  onClick={() => setInterviewType(type as InterviewType)}
                  className={`p-3.5 rounded-lg border text-left flex flex-col gap-2 transition-all ${
                    interviewType === type
                      ? "border-blue-600 bg-blue-50/50 text-blue-900 ring-1 ring-blue-600"
                      : "border-slate-200 hover:border-slate-300 text-slate-700"
                  }`}
                >
                  <Icon className="h-5 w-5 text-blue-600" />
                  <span className="text-sm font-medium">{label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty Level */}
          <div>
            <label className="block text-sm font-semibold text-slate-800">Difficulty Tier</label>
            <div className="grid grid-cols-3 gap-3 mt-1.5">
              {(["beginner", "intermediate", "advanced"] as const).map((diff) => (
                <button
                  type="button"
                  key={diff}
                  onClick={() => setDifficulty(diff)}
                  className={`py-2 px-3 rounded-lg border text-center text-sm font-medium capitalize transition-all ${
                    difficulty === diff
                      ? "border-blue-600 bg-blue-50 text-blue-900 ring-1 ring-blue-600"
                      : "border-slate-200 hover:border-slate-300 text-slate-700"
                  }`}
                >
                  {diff}
                </button>
              ))}
            </div>
          </div>

          {/* Attach CV */}
          <div>
            <label className="block text-sm font-semibold text-slate-800">
              Attach Uploaded CV (Optional)
            </label>
            <p className="text-xs text-slate-500 mb-1.5">
              The AI interviewer will adapt questions to test skills extracted from your resume.
            </p>
            <select
              value={selectedResumeId}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">No CV attached (General question pool)</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.original_filename} ({r.skills.length} confirmed skills)
                </option>
              ))}
            </select>
          </div>

          <Button type="submit" isLoading={isLoading} className="w-full py-3 text-base">
            Start Practice Interview
          </Button>
        </form>
      </Card>
    </div>
  );
};
