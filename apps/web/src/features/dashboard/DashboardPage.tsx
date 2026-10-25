import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { PlayCircle, Target, TrendingUp, CheckCircle2 } from "lucide-react";

interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
}

export const DashboardPage: React.FC = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/health/live")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to connect to backend");
        return res.json();
      })
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Welcome to CareerPilot</h1>
          <p className="text-slate-600 mt-1">
            AI-driven technical interview practice, live code assessment, and Skill Mastery tracking.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/interviews/new">
            <Button className="flex items-center gap-2">
              <PlayCircle className="h-4 w-4" />
              <span>Start New Interview</span>
            </Button>
          </Link>
        </div>
      </div>

      {/* System Status Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-medium text-blue-900">
            Backend API Status:
          </span>
          {loading ? (
            <span className="text-sm text-blue-600">Checking health...</span>
          ) : error ? (
            <span className="text-sm text-red-600">{error} (Is backend running?)</span>
          ) : (
            <span className="text-sm text-emerald-700 font-semibold">
              Connected ({health?.app_name} v{health?.version})
            </span>
          )}
        </div>
        <span className="text-xs text-blue-600 font-mono">Phase 0: Environment Ready</span>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Target Role" subtitle="Current career preparation focus">
          <div className="mt-2 flex items-center gap-3">
            <Target className="h-8 w-8 text-blue-600" />
            <div>
              <p className="font-semibold text-slate-900">Software Engineer (Backend)</p>
              <p className="text-xs text-slate-500">Configured in onboarding</p>
            </div>
          </div>
        </Card>

        <Card title="Skill Mastery" subtitle="Engine diagnose & target gaps">
          <div className="mt-2 flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-emerald-600" />
            <div>
              <p className="font-semibold text-slate-900">Evidence-based DAG</p>
              <p className="text-xs text-slate-500">Tracks Python, SQL, Algorithms</p>
            </div>
          </div>
        </Card>

        <Card title="Code Execution" subtitle="Judge0 isolated sandbox">
          <div className="mt-2 flex items-center gap-3">
            <CheckCircle2 className="h-8 w-8 text-indigo-600" />
            <div>
              <p className="font-semibold text-slate-900">Resource Bounded</p>
              <p className="text-xs text-slate-500">Monaco editor + test verification</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
