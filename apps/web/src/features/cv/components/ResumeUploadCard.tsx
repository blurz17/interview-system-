import React, { useRef, useState } from "react";
import { Upload, FileText, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { uploadResumeFile } from "../api/cv-api";
import { Resume } from "../types";
import { ApiError } from "../../../lib/api-client";

interface ResumeUploadCardProps {
  onUploadSuccess: (resume: Resume) => void;
}

export const ResumeUploadCard: React.FC<ResumeUploadCardProps> = ({ onUploadSuccess }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setErrorMessage(null);

    try {
      const resume = await uploadResumeFile(file);
      onUploadSuccess(resume);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Failed to upload and parse CV. Please check file format.");
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  return (
    <Card
      title="Upload Your CV / Resume"
      subtitle="Supported formats: PDF, DOCX, TXT (Maximum 10 MB)"
      className="border-dashed border-2 border-slate-300 hover:border-blue-400 transition-colors"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt"
        onChange={handleFileChange}
        className="hidden"
      />

      {errorMessage && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="py-8 text-center flex flex-col items-center justify-center space-y-4">
        <div className="h-14 w-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
          {isUploading ? (
            <Loader2 className="h-7 w-7 animate-spin" />
          ) : (
            <Upload className="h-7 w-7" />
          )}
        </div>

        <div>
          <p className="text-base font-semibold text-slate-800">
            {isUploading ? "Extracting skills from CV..." : "Select or drag your CV here"}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            CareerPilot extracts your technical skills, projects, and target role evidence.
          </p>
        </div>

        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          isLoading={isUploading}
          className="flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          <span>Browse File</span>
        </Button>
      </div>
    </Card>
  );
};
