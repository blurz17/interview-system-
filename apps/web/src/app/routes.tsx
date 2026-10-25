import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { LoginPage } from "../features/auth/LoginPage";
import { RegisterPage } from "../features/auth/RegisterPage";
import { ResumeManagementPage } from "../features/cv/ResumeManagementPage";
import { InterviewSetupPage } from "../features/interviews/InterviewSetupPage";
import { InterviewWorkspacePage } from "../features/interviews/InterviewWorkspacePage";
import { EvaluationReportPage } from "../features/evaluations/EvaluationReportPage";

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/resume" element={<ResumeManagementPage />} />
      <Route path="/interviews/new" element={<InterviewSetupPage />} />
      <Route path="/interviews/:id" element={<InterviewWorkspacePage />} />
      <Route path="/interviews/:id/report" element={<EvaluationReportPage />} />
      {/* Route placeholders for upcoming phases */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
