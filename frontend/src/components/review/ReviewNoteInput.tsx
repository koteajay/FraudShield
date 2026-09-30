import React from 'react';
import { FileText } from 'lucide-react';

interface ReviewNoteInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  maxLength?: number;
}

export const ReviewNoteInput: React.FC<ReviewNoteInputProps> = ({
  value,
  onChange,
  disabled = false,
  maxLength = 2000,
}) => {
  const currentLength = value.length;
  const isNearLimit = currentLength >= maxLength * 0.9;
  const isAtLimit = currentLength >= maxLength;

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    if (text.length <= maxLength) {
      onChange(text);
    }
  };

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <label
          htmlFor="reviewer-note-input"
          className="text-xs font-semibold text-slate-300 flex items-center gap-1.5"
        >
          <FileText className="w-3.5 h-3.5 text-blue-400" />
          <span>Reviewer Note</span>
          <span className="text-slate-500 font-normal">(optional)</span>
        </label>
        <span
          className={`text-[11px] font-mono ${
            isAtLimit
              ? 'text-rose-400 font-bold'
              : isNearLimit
              ? 'text-amber-400 font-semibold'
              : 'text-slate-400'
          }`}
          aria-live="polite"
        >
          {currentLength} / {maxLength}
        </span>
      </div>

      <textarea
        id="reviewer-note-input"
        rows={3}
        value={value}
        onChange={handleChange}
        disabled={disabled}
        maxLength={maxLength}
        placeholder="Enter your investigation findings, evidence review rationale, or customer verification details..."
        className="w-full rounded-xl bg-slate-950/80 border border-slate-800 p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed resize-none transition-colors"
      />
    </div>
  );
};
