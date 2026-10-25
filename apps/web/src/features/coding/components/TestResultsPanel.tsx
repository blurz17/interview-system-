import React, { useState } from "react";
import { CheckCircle2, XCircle, Clock, Lock, Cpu, Database } from "lucide-react";
import { CodingSubmissionPublic, TestResultPublic } from "../types";

interface TestResultsPanelProps {
  submission: CodingSubmissionPublic | null;
  results: TestResultPublic[];
  isLoading?: boolean;
}

export const TestResultsPanel: React.FC<TestResultsPanelProps> = ({
  submission,
  results,
  isLoading = false,
}) => {
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        <div className="inline-block animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent" />
        <p className="mt-3 text-sm font-medium">Executing code in sandbox & evaluating test cases...</p>
      </div>
    );
  }

  if (!submission && results.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center text-slate-400 text-sm">
        <Cpu className="h-8 w-8 mx-auto mb-2 text-slate-600" />
        <span>Click "Run & Submit" to execute your solution against test cases.</span>
      </div>
    );
  }

  const selectedTest = results[selectedIdx] || results[0];
  const allPassed = submission && submission.passed_tests === submission.total_tests;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg text-slate-200">
      {/* Summary Header */}
      <div className="px-5 py-3 bg-slate-950/80 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-sm">
            {allPassed ? (
              <span className="text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4" /> All Tests Passed
              </span>
            ) : (
              <span className="text-red-400 flex items-center gap-1.5">
                <XCircle className="h-4 w-4" /> Tests Incomplete
              </span>
            )}
          </span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono font-medium">
            {submission?.passed_tests || 0} / {submission?.total_tests || results.length} passed
          </span>
        </div>

        <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
          {submission?.runtime_ms !== undefined && submission?.runtime_ms !== null && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3 text-blue-400" />
              {submission.runtime_ms} ms
            </span>
          )}
          {submission?.memory_kb !== undefined && submission?.memory_kb !== null && (
            <span className="flex items-center gap-1">
              <Database className="h-3 w-3 text-indigo-400" />
              {submission.memory_kb} KB
            </span>
          )}
        </div>
      </div>

      {/* Test Case Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-950/40 overflow-x-auto">
        {results.map((r, idx) => {
          const isPassed = r.status === "passed";
          const isSelected = selectedIdx === idx;
          return (
            <button
              key={r.id || idx}
              type="button"
              onClick={() => setSelectedIdx(idx)}
              className={`px-4 py-2 text-xs font-medium flex items-center gap-2 border-b-2 transition-all whitespace-nowrap ${
                isSelected
                  ? "border-blue-500 bg-slate-800/60 text-white"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              }`}
            >
              {isPassed ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              ) : (
                <XCircle className="h-3.5 w-3.5 text-red-400" />
              )}
              <span>Case {idx + 1}</span>
              {r.is_hidden && <Lock className="h-3 w-3 text-slate-500" />}
            </button>
          );
        })}
      </div>

      {/* Selected Test Case Details */}
      {selectedTest && (
        <div className="p-5 space-y-4 text-xs font-mono">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-300">
                Case {selectedIdx + 1} Status:
              </span>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                  selectedTest.status === "passed"
                    ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                    : "bg-red-950 text-red-400 border border-red-800"
                }`}
              >
                {selectedTest.status}
              </span>
            </div>

            {selectedTest.execution_time_ms && (
              <span className="text-slate-400 text-[11px]">
                {selectedTest.execution_time_ms} ms
              </span>
            )}
          </div>

          {selectedTest.is_hidden ? (
            <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-4 text-slate-400 flex items-center gap-3">
              <Lock className="h-5 w-5 text-amber-500 shrink-0" />
              <div>
                <p className="font-medium text-slate-300">Hidden Evaluation Test Case</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Input data and expected output are protected for assessment integrity.
                </p>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Input */}
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                <span className="text-slate-400 text-[11px] block mb-1">Input</span>
                <pre className="text-slate-200 overflow-x-auto whitespace-pre-wrap">
                  {selectedTest.input_data || "(none)"}
                </pre>
              </div>

              {/* Expected Output */}
              <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3">
                <span className="text-slate-400 text-[11px] block mb-1">Expected Output</span>
                <pre className="text-slate-200 overflow-x-auto whitespace-pre-wrap">
                  {selectedTest.expected_output || "(none)"}
                </pre>
              </div>

              {/* Actual Output */}
              <div
                className={`rounded-lg p-3 border ${
                  selectedTest.status === "passed"
                    ? "bg-emerald-950/20 border-emerald-900/60 text-emerald-300"
                    : "bg-red-950/20 border-red-900/60 text-red-300"
                }`}
              >
                <span className="text-slate-400 text-[11px] block mb-1">Actual Output</span>
                <pre className="overflow-x-auto whitespace-pre-wrap">
                  {selectedTest.actual_output || "(no output or error)"}
                </pre>
              </div>
            </div>
          )}

          {selectedTest.error_category && (
            <div className="p-3 bg-red-950/30 border border-red-900/50 rounded-lg text-red-300 text-[11px]">
              <span className="font-bold">Error:</span> {selectedTest.error_category}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
