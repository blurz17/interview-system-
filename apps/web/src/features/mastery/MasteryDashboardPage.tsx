import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  Award,
  Sparkles,
  BookOpen,
  CheckCircle2,
  AlertCircle,
  PlayCircle,
  Zap,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import {
  getSkillMastery,
  getTrainingAssignments,
  generateTrainingAssignments,
  submitTrainingAttempt,
} from "./api/mastery-api";
import { TrainingAssignmentPublic, UserSkillMasteryPublic } from "./types";
import { ApiError } from "../../lib/api-client";

export const MasteryDashboardPage: React.FC = () => {
  const [masteryList, setMasteryList] = useState<UserSkillMasteryPublic[]>([]);
  const [assignments, setAssignments] = useState<TrainingAssignmentPublic[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [completingAssignmentId, setCompletingAssignmentId] = useState<string | null>(null);
  const [attemptScore, setAttemptScore] = useState<number>(85);
  const [attemptSummary, setAttemptSummary] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [m, a] = await Promise.all([getSkillMastery(), getTrainingAssignments()]);
      setMasteryList(m);
      setAssignments(a);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to load skill mastery data.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGenerateAssignments = async () => {
    setIsGenerating(true);
    setErrorMessage(null);
    try {
      const generated = await generateTrainingAssignments();
      setAssignments(generated);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to generate recommendations.");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCompleteAttempt = async (assignmentId: string) => {
    try {
      await submitTrainingAttempt(assignmentId, {
        score: attemptScore,
        result_summary: attemptSummary.trim() || "Completed targeted practice assignment.",
      });
      setCompletingAssignmentId(null);
      setAttemptSummary("");
      // Reload both assignments and mastery scores to reflect the update!
      await loadData();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to submit attempt.");
      }
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent" />
        <p className="mt-4 text-slate-600 font-medium">Loading Skill Mastery graph and assignments...</p>
      </div>
    );
  }

  // Group mastery by category
  const categories = Array.from(new Set(masteryList.map((m) => m.category)));
  const totalEvidence = masteryList.reduce((acc, m) => acc + m.evidence_count, 0);
  const avgMastery =
    masteryList.length > 0
      ? Math.round((masteryList.reduce((acc, m) => acc + m.mastery_score, 0) / masteryList.length) * 100)
      : 0;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Skill Mastery Engine</h1>
          <p className="text-slate-600 text-sm mt-1">
            Evidence-based capability tracking with exponential recency updates (M_new = (1-α)M_old + αS).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            onClick={handleGenerateAssignments}
            isLoading={isGenerating}
            className="flex items-center gap-2"
          >
            <Sparkles className="h-4 w-4" />
            <span>Generate Targeted Practice</span>
          </Button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Metrics Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-xl bg-blue-50 text-blue-600">
              <Award className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Mastery</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{avgMastery}%</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-xl bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tracked Skills</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{masteryList.length} Skills</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-xl bg-indigo-50 text-indigo-600">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Confirmed Evidence</p>
              <p className="text-2xl font-bold text-slate-900 mt-0.5">{totalEvidence} Records</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Active Training Assignments Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-blue-600" />
            <span>Targeted Training Assignments</span>
          </h2>
          <span className="text-xs text-slate-500 font-medium">
            {assignments.filter((a) => a.status !== "completed").length} Active Drills
          </span>
        </div>

        {assignments.length === 0 ? (
          <Card className="text-center py-8">
            <Sparkles className="h-8 w-8 mx-auto mb-2 text-blue-400" />
            <p className="text-sm font-medium text-slate-700">No active practice assignments yet.</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Click "Generate Targeted Practice" above to analyze your skill gaps and create personalized drills.
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {assignments.map((assignment) => {
              const isCompleted = assignment.status === "completed";
              const isFormOpen = completingAssignmentId === assignment.id;
              return (
                <Card
                  key={assignment.id}
                  className={`flex flex-col justify-between transition-all ${
                    isCompleted ? "bg-slate-50 border-slate-200 opacity-75" : "border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-blue-100 text-blue-800">
                        {assignment.skill_name}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                          isCompleted
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-amber-100 text-amber-800"
                        }`}
                      >
                        {assignment.status}
                      </span>
                    </div>

                    <h3 className="font-bold text-slate-900 text-base">{assignment.title}</h3>
                    <p className="text-xs text-slate-600 leading-relaxed">{assignment.description}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex flex-col gap-2">
                    {!isCompleted && !isFormOpen && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => setCompletingAssignmentId(assignment.id)}
                        className="w-full text-xs"
                      >
                        Record Practice Attempt
                      </Button>
                    )}

                    {isFormOpen && (
                      <div className="bg-slate-50 p-3 rounded-lg space-y-2 border border-slate-200 text-xs">
                        <div>
                          <label className="font-semibold text-slate-700 block mb-1">
                            Simulated Score ({attemptScore}%)
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={attemptScore}
                            onChange={(e) => setAttemptScore(Number(e.target.value))}
                            className="w-full"
                          />
                        </div>
                        <input
                          type="text"
                          value={attemptSummary}
                          onChange={(e) => setAttemptSummary(e.target.value)}
                          placeholder="Summary (e.g., Passed all edge cases)"
                          className="w-full p-2 border border-slate-300 rounded text-xs bg-white"
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleCompleteAttempt(assignment.id)}
                            className="flex-1 text-xs py-1"
                          >
                            Submit Attempt
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setCompletingAssignmentId(null)}
                            className="text-xs py-1"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}

                    {isCompleted && (
                      <div className="flex items-center gap-1.5 text-xs text-emerald-700 font-semibold">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Completed</span>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>

      {/* Skill Mastery Graph & Category Progress */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-600" />
          <span>Competency & Skill Profile</span>
        </h2>

        {masteryList.length === 0 ? (
          <Card className="text-center py-12">
            <Award className="h-10 w-10 text-slate-300 mx-auto mb-2" />
            <h3 className="font-semibold text-slate-800">No Skill Evidence Recorded Yet</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
              Start an interview session or practice assignment. Every observed performance updates your skill graph.
            </p>
            <Link to="/interviews/new" className="mt-4 inline-block">
              <Button className="flex items-center gap-2">
                <PlayCircle className="h-4 w-4" />
                <span>Start Practice Interview</span>
              </Button>
            </Link>
          </Card>
        ) : (
          <div className="space-y-6">
            {categories.map((category) => {
              const skillsInCat = masteryList.filter((m) => m.category === category);
              return (
                <Card key={category} title={category.replace(/_/g, " ").toUpperCase()}>
                  <div className="divide-y divide-slate-100">
                    {skillsInCat.map((m) => {
                      const percentage = Math.round(m.mastery_score * 100);
                      const isHighConf = m.confidence >= 0.8;
                      const isModConf = m.confidence >= 0.6;
                      return (
                        <div key={m.id} className="py-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
                          <div className="w-48 shrink-0">
                            <span className="font-semibold text-slate-900 text-sm">{m.skill_name}</span>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span
                                className={`px-2 py-0.2 rounded text-[10px] font-bold uppercase ${
                                  isHighConf
                                    ? "bg-emerald-100 text-emerald-800"
                                    : isModConf
                                    ? "bg-blue-100 text-blue-800"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                              >
                                {isHighConf ? "High Confidence" : isModConf ? "Moderate" : "Preliminary"}
                              </span>
                              <span className="text-[11px] text-slate-400 font-mono">
                                ({m.evidence_count} evidence)
                              </span>
                            </div>
                          </div>

                          <div className="flex-1 flex items-center gap-3">
                            <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                              <div
                                className={`h-2.5 rounded-full transition-all ${
                                  percentage >= 80
                                    ? "bg-emerald-500"
                                    : percentage >= 65
                                    ? "bg-blue-600"
                                    : "bg-amber-500"
                                }`}
                                style={{ width: `${percentage}%` }}
                              />
                            </div>
                            <span className="font-bold text-xs text-slate-800 w-10 text-right font-mono">
                              {percentage}%
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
