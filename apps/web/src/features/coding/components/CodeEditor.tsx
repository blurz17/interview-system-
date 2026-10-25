import React from "react";
import Editor from "@monaco-editor/react";
import { Play, RotateCcw, Code2 } from "lucide-react";
import { Button } from "../../../components/ui/Button";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onReset?: () => void;
  isSubmitting?: boolean;
  language?: string;
  readOnly?: boolean;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  onSubmit,
  onReset,
  isSubmitting = false,
  language = "python",
  readOnly = false,
}) => {
  return (
    <div className="flex flex-col h-full border border-slate-700 rounded-xl overflow-hidden shadow-lg bg-[#1e1e1e]">
      {/* Editor Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#252526] border-b border-slate-800 text-slate-300 text-xs">
        <div className="flex items-center gap-2">
          <Code2 className="h-4 w-4 text-blue-400" />
          <span className="font-semibold text-white">Solution Editor</span>
          <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[11px] font-mono">
            {language.toUpperCase()} 3.11
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onReset && (
            <button
              type="button"
              onClick={onReset}
              disabled={isSubmitting || readOnly}
              title="Reset starter template"
              className="p-1.5 hover:bg-slate-700 text-slate-400 hover:text-white rounded transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}

          <Button
            size="sm"
            variant="primary"
            onClick={onSubmit}
            isLoading={isSubmitting}
            disabled={readOnly || isSubmitting || !value.trim()}
            className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium px-3 py-1 text-xs"
          >
            <Play className="h-3 w-3 fill-current" />
            <span>Run & Submit</span>
          </Button>
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 min-h-[360px]">
        <Editor
          height="100%"
          language={language}
          value={value}
          theme="vs-dark"
          onChange={(val) => onChange(val || "")}
          options={{
            readOnly,
            fontSize: 14,
            tabSize: 4,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            lineNumbers: "on",
            renderLineHighlight: "all",
          }}
        />
      </div>
    </div>
  );
};
