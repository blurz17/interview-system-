import React, { useEffect, useState } from "react";
import { FileText, Trash2, Calendar, AlertCircle } from "lucide-react";
import { ResumeUploadCard } from "./components/ResumeUploadCard";
import { SkillReviewTable } from "./components/SkillReviewTable";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { deleteResumeFile, getResumes } from "./api/cv-api";
import { Resume } from "./types";

export const ResumeManagementPage: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadResumes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getResumes();
      setResumes(data);
      if (data.length > 0 && !selectedResumeId) {
        setSelectedResumeId(data[0].id);
      }
    } catch {
      setError("Failed to load CVs. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const handleUploadSuccess = (newResume: Resume) => {
    setResumes((prev) => [newResume, ...prev]);
    setSelectedResumeId(newResume.id);
  };

  const handleSkillsUpdated = (updatedResume: Resume) => {
    setResumes((prev) =>
      prev.map((r) => (r.id === updatedResume.id ? updatedResume : r))
    );
  };

  const handleDelete = async (resumeId: string) => {
    if (!window.confirm("Are you sure you want to delete this CV and its extracted skills?")) {
      return;
    }
    await deleteResumeFile(resumeId);
    setResumes((prev) => prev.filter((r) => r.id !== resumeId));
    if (selectedResumeId === resumeId) {
      setSelectedResumeId(null);
    }
  };

  const activeResume = resumes.find((r) => r.id === selectedResumeId) || resumes[0];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">CV Management & Skill Extraction</h1>
        <p className="text-slate-600 mt-1">
          Upload your CV to extract technical competencies, or review and refine your confirmed skills.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Upload Zone */}
      <ResumeUploadCard onUploadSuccess={handleUploadSuccess} />

      {/* Resumes List & Skill Review */}
      {isLoading ? (
        <div className="py-12 text-center text-slate-500">Loading CV data...</div>
      ) : resumes.length === 0 ? (
        <Card className="text-center py-8">
          <FileText className="h-10 w-10 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-600 text-sm">No CV uploaded yet. Upload one above to get started.</p>
        </Card>
      ) : (
        <div className="space-y-6">
          {/* Active CV Header */}
          {activeResume && (
            <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center shrink-0">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{activeResume.original_filename}</h3>
                  <div className="flex items-center gap-4 text-xs text-slate-500 mt-0.5">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5" />
                      {new Date(activeResume.created_at).toLocaleDateString()}
                    </span>
                    <span>{(activeResume.file_size_bytes / 1024).toFixed(1)} KB</span>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 font-medium rounded-full">
                      {activeResume.skills.length} skills identified
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleDelete(activeResume.id)}
                  className="text-red-600 hover:bg-red-50 hover:border-red-200 flex items-center gap-1.5"
                >
                  <Trash2 className="h-4 w-4" />
                  <span>Delete CV</span>
                </Button>
              </div>
            </div>
          )}

          {/* Extracted Skills Review */}
          {activeResume && (
            <SkillReviewTable
              resume={activeResume}
              onSkillsUpdated={handleSkillsUpdated}
            />
          )}
        </div>
      )}
    </div>
  );
};
