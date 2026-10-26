import React, { useState, useEffect } from "react";
import {
  Target,
  Link as LinkIcon,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  Sparkles,
  MapPin,
  Clock,
  Building,
  Upload,
  ChevronDown,
  ChevronUp,
  Cpu,
} from "lucide-react";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { getResumes } from "../cv/api/cv-api";
import { Resume } from "../cv/types";
import { analyzeJobFit, fetchJobDetails } from "./api/job-hunter-api";
import { FetchJobResponse, JobHunterAnalysisResult } from "./types";

export const JobHunterPage: React.FC = () => {
  // Input State
  const [cvSource, setCvSource] = useState<"existing" | "file" | "text">("existing");
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>("");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [cvText, setCvText] = useState<string>("");

  const [jobMode, setJobMode] = useState<"url" | "text">("url");
  const [jobUrl, setJobUrl] = useState<string>("https://www.linkedin.com/jobs/view/4479952015/");
  const [jobText, setJobText] = useState<string>("");
  const [isFetchingJob, setIsFetchingJob] = useState<boolean>(false);
  const [fetchedJob, setFetchedJob] = useState<FetchJobResponse | null>(null);

  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  const [hfToken, setHfToken] = useState<string>("");

  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<JobHunterAnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Copy Feedback
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [copiedMessage, setCopiedMessage] = useState<boolean>(false);

  useEffect(() => {
    // Load available resumes from user's account
    getResumes()
      .then((data) => {
        setResumes(data);
        if (data.length > 0) {
          setSelectedResumeId(data[0].id);
        } else {
          setCvSource("file");
        }
      })
      .catch(() => {
        setCvSource("file");
      });
  }, []);

  const handleFetchJob = async () => {
    if (!jobUrl.trim()) return;
    setIsFetchingJob(true);
    setErrorMessage(null);
    try {
      const data = await fetchJobDetails(jobUrl.trim());
      setFetchedJob(data);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to fetch job posting from URL.");
    } finally {
      setIsFetchingJob(false);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const formData = new FormData();

      // CV input
      if (cvSource === "existing" && selectedResumeId) {
        formData.append("resume_id", selectedResumeId);
      } else if (cvSource === "file" && uploadedFile) {
        formData.append("cv_file", uploadedFile);
      } else if (cvSource === "text" && cvText.trim()) {
        formData.append("cv_text", cvText.trim());
      } else {
        throw new Error("Please provide a CV (select an existing one, upload a file, or paste text).");
      }

      // Job input
      if (jobMode === "url") {
        if (!jobUrl.trim()) throw new Error("Please enter a valid job URL.");
        formData.append("job_url", jobUrl.trim());
        if (fetchedJob?.description) {
          formData.append("job_text", fetchedJob.description);
        }
      } else {
        if (!jobText.trim()) throw new Error("Please paste job requirements.");
        formData.append("job_text", jobText.trim());
      }

      // HF Token
      if (hfToken.trim()) {
        formData.append("hf_token", hfToken.trim());
      }

      const result = await analyzeJobFit(formData);
      setAnalysisResult(result);
    } catch (err: any) {
      setErrorMessage(err.message || "Analysis failed. Please check inputs.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const copyBullet = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const copyOutreach = () => {
    if (!analysisResult) return;
    navigator.clipboard.writeText(analysisResult.recruiter_outreach_message);
    setCopiedMessage(true);
    setTimeout(() => setCopiedMessage(false), 2000);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <span className="p-2 bg-blue-100 text-blue-700 rounded-lg">
            <Target className="h-6 w-6" />
          </span>
          <h1 className="text-2xl font-bold text-slate-900">Job Hunter & Match Engine</h1>
        </div>
        <p className="text-slate-600 mt-1 max-w-3xl">
          Compare candidate CVs directly against real-world job postings. Evaluates hard engineering
          requirements, verifies contract & location eligibility, checks timezone overlap, and
          generates tailored ATS bullet points and outreach messages.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form: Inputs */}
        <div className="lg:col-span-5 space-y-6">
          <Card title="Input Parameters" subtitle="Configure CV and Target Job Specification">
            <form onSubmit={handleAnalyze} className="space-y-5">
              {/* CV Source Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  1. Candidate CV
                </label>
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <button
                    type="button"
                    onClick={() => setCvSource("existing")}
                    disabled={resumes.length === 0}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition ${
                      cvSource === "existing"
                        ? "bg-blue-50 border-blue-600 text-blue-700 shadow-sm"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    } ${resumes.length === 0 ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    Saved CV ({resumes.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setCvSource("file")}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition ${
                      cvSource === "file"
                        ? "bg-blue-50 border-blue-600 text-blue-700 shadow-sm"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    Upload File
                  </button>
                  <button
                    type="button"
                    onClick={() => setCvSource("text")}
                    className={`py-2 px-3 text-xs font-medium rounded-lg border text-center transition ${
                      cvSource === "text"
                        ? "bg-blue-50 border-blue-600 text-blue-700 shadow-sm"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    Paste Text
                  </button>
                </div>

                {cvSource === "existing" && (
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.original_filename} (Uploaded {new Date(r.created_at).toLocaleDateString()})
                      </option>
                    ))}
                  </select>
                )}

                {cvSource === "file" && (
                  <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:border-blue-400 transition">
                    <input
                      type="file"
                      id="cvFileInput"
                      accept=".pdf,.docx,.txt"
                      onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                      className="hidden"
                    />
                    <label htmlFor="cvFileInput" className="cursor-pointer block">
                      <Upload className="h-6 w-6 text-slate-400 mx-auto mb-1.5" />
                      <span className="text-xs font-medium text-blue-600 hover:underline">
                        {uploadedFile ? uploadedFile.name : "Choose PDF, DOCX or TXT file"}
                      </span>
                      <p className="text-[11px] text-slate-400 mt-1">Maximum size 10MB</p>
                    </label>
                  </div>
                )}

                {cvSource === "text" && (
                  <textarea
                    rows={4}
                    value={cvText}
                    onChange={(e) => setCvText(e.target.value)}
                    placeholder="Paste candidate resume or raw experience text..."
                    className="w-full text-xs font-mono border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                )}
              </div>

              {/* Job Source */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  2. Target Job Requirements
                </label>
                <div className="flex gap-2 mb-3">
                  <button
                    type="button"
                    onClick={() => setJobMode("url")}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-lg border transition ${
                      jobMode === "url"
                        ? "bg-blue-50 border-blue-600 text-blue-700"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    Job URL (LinkedIn/Career)
                  </button>
                  <button
                    type="button"
                    onClick={() => setJobMode("text")}
                    className={`flex-1 py-1.5 text-xs font-medium rounded-lg border transition ${
                      jobMode === "text"
                        ? "bg-blue-50 border-blue-600 text-blue-700"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    Paste Requirements Text
                  </button>
                </div>

                {jobMode === "url" ? (
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <div className="relative flex-1">
                        <LinkIcon className="h-4 w-4 text-slate-400 absolute left-3 top-3" />
                        <input
                          type="url"
                          value={jobUrl}
                          onChange={(e) => setJobUrl(e.target.value)}
                          placeholder="https://www.linkedin.com/jobs/view/..."
                          className="w-full text-xs pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                      </div>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleFetchJob}
                        disabled={isFetchingJob || !jobUrl.trim()}
                        className="text-xs shrink-0"
                      >
                        {isFetchingJob ? "Fetching..." : "Inspect"}
                      </Button>
                    </div>

                    {fetchedJob && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                        <div className="font-semibold text-slate-900">{fetchedJob.title}</div>
                        <div className="text-slate-500 flex items-center gap-3">
                          <span className="flex items-center gap-1">
                            <Building className="h-3 w-3" /> {fetchedJob.company}
                          </span>
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" /> {fetchedJob.location}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 line-clamp-2 mt-1">
                          {fetchedJob.description.slice(0, 150)}...
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <textarea
                    rows={5}
                    value={jobText}
                    onChange={(e) => setJobText(e.target.value)}
                    placeholder="Paste full job description, required skills, and location constraints..."
                    className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                )}
              </div>

              {/* Advanced HF Settings */}
              <div>
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 font-medium"
                >
                  <Cpu className="h-3.5 w-3.5" />
                  <span>Hugging Face AI Engine Settings</span>
                  {showAdvanced ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                </button>
                {showAdvanced && (
                  <div className="mt-2 p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                    <label className="block text-[11px] font-semibold text-slate-600">
                      Hugging Face API Token (Optional)
                    </label>
                    <input
                      type="password"
                      value={hfToken}
                      onChange={(e) => setHfToken(e.target.value)}
                      placeholder="hf_..."
                      className="w-full text-xs border border-slate-300 rounded-md p-2 bg-white"
                    />
                    <p className="text-[10px] text-slate-500">
                      Leave blank to run with CareerPilot's built-in Scikit/NLP engine, or enter your token to enable Llama-3.1 cloud reasoning.
                    </p>
                  </div>
                )}
              </div>

              <Button
                type="submit"
                disabled={isAnalyzing}
                className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-sm"
              >
                {isAnalyzing ? (
                  <>
                    <span className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    <span>Analyzing Job Fit & Matrix...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Analyze Fit & Generate Strategy</span>
                  </>
                )}
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Column: Results */}
        <div className="lg:col-span-7 space-y-6">
          {!analysisResult ? (
            <Card className="text-center py-16">
              <div className="h-16 w-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Target className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">No Analysis Executed Yet</h3>
              <p className="text-sm text-slate-500 max-w-md mx-auto mt-1.5">
                Select your CV on the left, enter a job URL or paste requirements, and click
                "Analyze Fit" to view deep evaluation metrics and actionable recommendations.
              </p>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Scorecard Header */}
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-1 rounded-full">
                      {analysisResult.job_meta.company}
                    </span>
                    <h2 className="text-xl font-bold text-slate-900 mt-1.5">
                      {analysisResult.job_meta.title}
                    </h2>
                    <div className="text-xs text-slate-500 flex items-center gap-2 mt-1">
                      <MapPin className="h-3.5 w-3.5" />
                      <span>{analysisResult.job_meta.location}</span>
                      {analysisResult.job_meta.url && (
                        <a
                          href={analysisResult.job_meta.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-600 hover:underline ml-2"
                        >
                          View Posting ↗
                        </a>
                      )}
                    </div>
                  </div>
                  <div className="text-right shrink-0">
                    <div className="text-4xl font-extrabold text-blue-600">
                      {analysisResult.overall_match_score}%
                    </div>
                    <span
                      className={`inline-block mt-1 text-xs font-semibold px-2.5 py-1 rounded-full ${
                        analysisResult.location_eligible
                          ? "bg-green-100 text-green-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {analysisResult.verdict}
                    </span>
                  </div>
                </div>

                {/* Eligibility & Timezone Alerts */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  <div
                    className={`p-3.5 rounded-xl border text-xs space-y-1 ${
                      analysisResult.location_eligible
                        ? "bg-green-50/70 border-green-200 text-green-900"
                        : "bg-amber-50/70 border-amber-200 text-amber-900"
                    }`}
                  >
                    <div className="font-semibold flex items-center gap-1.5">
                      {analysisResult.location_eligible ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-amber-600" />
                      )}
                      <span>Location / Contract Feasibility</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">{analysisResult.location_notes}</p>
                  </div>

                  <div className="p-3.5 rounded-xl border border-blue-200 bg-blue-50/60 text-blue-900 text-xs space-y-1">
                    <div className="font-semibold flex items-center gap-1.5">
                      <Clock className="h-4 w-4 text-blue-600" />
                      <span>Timezone Collaboration (CET)</span>
                    </div>
                    <p className="text-[11px] leading-relaxed">{analysisResult.timezone_notes}</p>
                  </div>
                </div>
              </div>

              {/* Hard Requirements Evaluation Matrix */}
              <Card title="Requirements Evaluation Matrix" subtitle="Detailed audit of hard technical criteria">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                        <th className="pb-3">Requirement</th>
                        <th className="pb-3 text-center">Status</th>
                        <th className="pb-3">Weight</th>
                        <th className="pb-3">Candidate CV Evidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {analysisResult.hard_requirements_analysis.map((req, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/70 transition">
                          <td className="py-3 font-medium text-slate-900 pr-2">{req.requirement}</td>
                          <td className="py-3 text-center px-2">
                            {req.status === "Passed" && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] bg-green-100 text-green-800">
                                <CheckCircle2 className="h-3 w-3" /> Passed
                              </span>
                            )}
                            {req.status === "Partial" && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] bg-amber-100 text-amber-800">
                                <AlertTriangle className="h-3 w-3" /> Partial
                              </span>
                            )}
                            {req.status === "Missing" && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-semibold text-[11px] bg-red-100 text-red-800">
                                <XCircle className="h-3 w-3" /> Missing
                              </span>
                            )}
                          </td>
                          <td className="py-3 text-slate-500 whitespace-nowrap">{req.weight}</td>
                          <td className="py-3 text-slate-600 max-w-xs">{req.cv_evidence}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              {/* Bonus Skills */}
              <Card title="Bonus & Nice-to-Have Skills" subtitle="Value-add proficiencies identified">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {analysisResult.bonus_points_analysis.map((b, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2.5"
                    >
                      {b.matched ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0 mt-0.5" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border border-slate-300 shrink-0 mt-0.5" />
                      )}
                      <div>
                        <div className="text-xs font-semibold text-slate-800">{b.skill}</div>
                        <div className="text-[11px] text-slate-500">{b.notes}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Tailored CV Bullets */}
              <Card
                title="Recommended Tailored CV Bullets"
                subtitle="Quantified, ATS-optimized achievement statements for your CV"
              >
                <div className="space-y-3">
                  {analysisResult.tailored_cv_bullets_to_add.map((bullet, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-start justify-between gap-3 group hover:border-blue-300 transition"
                    >
                      <p className="text-xs text-slate-800 leading-relaxed">• {bullet}</p>
                      <button
                        type="button"
                        onClick={() => copyBullet(bullet, idx)}
                        className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-white rounded-lg transition shrink-0"
                        title="Copy bullet"
                      >
                        {copiedIndex === idx ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Recruiter Outreach Pitch */}
              <Card
                title="High-Converting Recruiter Outreach Message"
                subtitle="Personalized LinkedIn message tailored to the hiring team"
              >
                <div className="relative bg-slate-900 text-slate-100 p-4 rounded-xl text-xs font-mono leading-relaxed overflow-x-auto">
                  <button
                    type="button"
                    onClick={copyOutreach}
                    className="absolute top-3 right-3 py-1 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-lg flex items-center gap-1.5 transition"
                  >
                    {copiedMessage ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-green-400" />
                        <span>Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" />
                        <span>Copy Pitch</span>
                      </>
                    )}
                  </button>
                  <pre className="whitespace-pre-wrap font-sans text-xs">
                    {analysisResult.recruiter_outreach_message}
                  </pre>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
