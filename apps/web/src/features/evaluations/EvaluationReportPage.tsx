import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Award,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  TrendingUp,
  FileCheck,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { getEvaluationReport, evaluateSession } from "./api/evaluations-api";
import { EvaluationReportPublic } from "./types";
import { ApiError } from "../../lib/api-client";

export const EvaluationReportPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [report, setReport] = useState<EvaluationReportPublic | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchReport = (force = false) => {
    if (!id) return;
    if (force) setIsRegenerating(true);
    else setIsLoading(true);

    const call = force ? evaluateSession(id) : getEvaluationReport(id);

    call
      .then((data) => {
        setReport(data);
        setIsLoading(false);
        setIsRegenerating(false);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setErrorMessage(err.message);
        } else {
          setErrorMessage("Failed to load evaluation report.");
        }
        setIsLoading(false);
        setIsRegenerating(false);
      });
  };

  useEffect(() => {
    fetchReport();
  }, [id]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent" />
        <p className="mt-4 text-slate-600 font-medium">
          Compiling evaluation report and verifying skill evidence...
        </p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-800 mt-3">Report Unavailable</h2>
        <p className="text-slate-600 mt-1">{errorMessage || "Could not generate report."}</p>
        <Link to="/dashboard" className="mt-4 inline-block">
          <Button variant="outline">Return to Dashboard</Button>
        </Link>
      </div>
    );
  }

  const score = report.overall_score;
  const scoreColor =
    score >= 85 ? "text-emerald-600" : score >= 70 ? "text-blue-600" : "text-amber-600";
  const scoreBadgeBg =
    score >= 85
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : score >= 70
      ? "bg-blue-50 text-blue-800 border-blue-200"
      : "bg-amber-50 text-amber-800 border-amber-200";

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      {/* Top Navigation & Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <Link
            to="/dashboard"
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition-colors mb-1"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Dashboard</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">Performance Evaluation Report</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200 font-mono">
              Rubric {report.rubric_version}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchReport(true)}
            isLoading={isRegenerating}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Re-evaluate</span>
          </Button>
          <Link to="/dashboard">
            <Button variant="primary" size="sm">
              Dashboard
            </Button>
          </Link>
        </div>
      </div>

      {/* Hero Scorecard Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-5">
          <div className="h-20 w-20 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center shrink-0">
            <Award className="h-10 w-10 text-blue-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-4xl font-extrabold ${scoreColor}`}>{score}</span>
              <span className="text-xl text-slate-400 font-medium">/ 100</span>
              <span className={`ml-2 px-3 py-1 rounded-full text-xs font-bold border uppercase tracking-wider ${scoreBadgeBg}`}>
                {score >= 85 ? "Advanced / Interview Ready" : score >= 70 ? "Competent / On Track" : "Needs Targeted Focus"}
              </span>
            </div>
            <p className="text-sm text-slate-600 mt-2 max-w-xl">
              {report.summary}
            </p>
          </div>
        </div>

        <div className="border-t md:border-t-0 md:border-l border-slate-200 pt-4 md:pt-0 md:pl-6 text-xs text-slate-500 space-y-2 shrink-0">
          <div className="flex items-center gap-2">
            <FileCheck className="h-4 w-4 text-emerald-600" />
            <span>Status: <strong className="text-slate-800 capitalize">{report.evaluation_status}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-blue-600" />
            <span>Traceable Evidence Count: <strong className="text-slate-800">{report.skill_evidences.length}</strong></span>
          </div>
        </div>
      </div>

      {/* Strengths & Weaknesses 2-Column Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <Card title="Demonstrated Strengths" className="border-emerald-100 bg-emerald-50/20">
          <ul className="space-y-3 mt-2 text-sm text-slate-800">
            {report.strengths.map((st, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                <span>{st}</span>
              </li>
            ))}
          </ul>
        </Card>

        {/* Growth Areas */}
        <Card title="Areas for Growth & Refinement" className="border-amber-100 bg-amber-50/20">
          <ul className="space-y-3 mt-2 text-sm text-slate-800">
            {report.weaknesses.map((w, idx) => (
              <li key={idx} className="flex items-start gap-2.5">
                <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <span>{w}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* Traceable Skill Evidence Breakdown */}
      <Card
        title="Skill Evidence & Competency Breakdown"
        subtitle="Every score traces directly to objective code executions or technical dialogue observations."
      >
        <div className="overflow-x-auto mt-4">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-50/60">
                <th className="py-3 px-4">Skill / Competency</th>
                <th className="py-3 px-4">Demonstrated Score</th>
                <th className="py-3 px-4">Evidence Type</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Observation Basis</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {report.skill_evidences.map((ev) => (
                <tr key={ev.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-3.5 px-4 font-semibold text-slate-900">
                    {ev.skill_name}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        ev.score >= 80
                          ? "bg-emerald-100 text-emerald-800"
                          : ev.score >= 65
                          ? "bg-blue-100 text-blue-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {ev.score}%
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-xs font-mono text-slate-600 capitalize">
                    {ev.evidence_type.replace(/_/g, " ")}
                  </td>
                  <td className="py-3.5 px-4 text-xs font-mono text-slate-600">
                    {Math.round(ev.confidence * 100)}%
                  </td>
                  <td className="py-3.5 px-4 text-xs text-slate-600 max-w-md">
                    {ev.explanation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Actionable Recommendations */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-950 text-white rounded-2xl p-6 shadow-md flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-blue-300 text-xs font-semibold uppercase tracking-wider">
            <TrendingUp className="h-4 w-4" />
            <span>Recommended Next Actions</span>
          </div>
          <h3 className="text-lg font-bold">Personalized Skill Mastery Assignments</h3>
          <ul className="text-sm text-slate-200 space-y-1.5 list-disc list-inside">
            {report.recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>

        <Link to="/dashboard" className="shrink-0">
          <Button variant="primary" className="bg-white text-blue-950 hover:bg-slate-100 flex items-center gap-2">
            <span>Continue Preparation</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </div>
    </div>
  );
};
