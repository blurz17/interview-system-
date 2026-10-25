import React, { useEffect, useState } from "react";
import { Check, Trash2, Plus, Sparkles } from "lucide-react";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { Resume, ResumeSkill, Skill } from "../types";
import { getAvailableSkills, updateResumeSkills } from "../api/cv-api";

interface SkillReviewTableProps {
  resume: Resume;
  onSkillsUpdated: (updatedResume: Resume) => void;
}

export const SkillReviewTable: React.FC<SkillReviewTableProps> = ({
  resume,
  onSkillsUpdated,
}) => {
  const [selectedSlugs, setSelectedSlugs] = useState<string[]>(
    resume.skills.map((s) => s.skill_slug)
  );
  const [catalog, setCatalog] = useState<Skill[]>([]);
  const [newSkillSlug, setNewSkillSlug] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setSelectedSlugs(resume.skills.map((s) => s.skill_slug));
    setHasChanges(false);
  }, [resume]);

  useEffect(() => {
    getAvailableSkills().then((skills) => setCatalog(skills));
  }, []);

  const handleRemoveSkill = (slug: string) => {
    setSelectedSlugs((prev) => prev.filter((s) => s !== slug));
    setHasChanges(true);
  };

  const handleAddSkill = () => {
    if (!newSkillSlug || selectedSlugs.includes(newSkillSlug)) return;
    setSelectedSlugs((prev) => [...prev, newSkillSlug]);
    setNewSkillSlug("");
    setHasChanges(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await updateResumeSkills(resume.id, selectedSlugs);
      onSkillsUpdated(updated);
      setHasChanges(false);
    } finally {
      setIsSaving(false);
    }
  };

  // Find remaining catalog skills
  const availableToAdd = catalog.filter((s) => !selectedSlugs.includes(s.slug));

  return (
    <Card
      title="Extracted Skills & Evidence"
      subtitle={`Review and confirm skills extracted from "${resume.original_filename}"`}
    >
      <div className="space-y-6">
        {/* Skills Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="px-4 py-3">Skill</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Section</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Evidence Found</th>
                <th className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {selectedSlugs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                    No skills selected. Use the selector below to add skills.
                  </td>
                </tr>
              ) : (
                selectedSlugs.map((slug) => {
                  const existing: ResumeSkill | undefined = resume.skills.find(
                    (s) => s.skill_slug === slug
                  );
                  const catalogItem: Skill | undefined = catalog.find((s) => s.slug === slug);
                  const skillName = existing?.skill_name || catalogItem?.name || slug;
                  const category = existing?.category || catalogItem?.category || "General";
                  const confidence = existing?.extraction_confidence ?? 1.0;
                  const section = existing?.source_section || "Manual Addition";
                  const evidence = existing?.evidence_text || "Confirmed by candidate";

                  return (
                    <tr key={slug} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-900 flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5 text-blue-500" />
                        <span>{skillName}</span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 capitalize">
                        <span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">
                          {category.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs">{section}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded ${
                            confidence >= 0.9
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-blue-50 text-blue-700"
                          }`}
                        >
                          {Math.round(confidence * 100)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs max-w-xs truncate" title={evidence}>
                        {evidence}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(slug)}
                          className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                          title="Remove skill"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Add Skill Control */}
        <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <select
              value={newSkillSlug}
              onChange={(e) => setNewSkillSlug(e.target.value)}
              className="text-sm px-3 py-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a skill to add...</option>
              {availableToAdd.map((s) => (
                <option key={s.slug} value={s.slug}>
                  {s.name} ({s.category})
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAddSkill}
              disabled={!newSkillSlug}
              className="flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              <span>Add Skill</span>
            </Button>
          </div>

          <Button
            onClick={handleSave}
            isLoading={isSaving}
            disabled={!hasChanges}
            className="flex items-center gap-2 w-full sm:w-auto"
          >
            <Check className="h-4 w-4" />
            <span>Save & Confirm Skills</span>
          </Button>
        </div>
      </div>
    </Card>
  );
};
