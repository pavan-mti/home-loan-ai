import React from 'react';
import FieldInput from './FieldInput';
import ConfidenceBadge from './ConfidenceBadge';

export default function DynamicFieldCard({ label, value, confidence, type, onChange }) {
  const isTextArea = type === 'long_text' || type === 'textarea';

  return (
    <div className={`flex flex-col gap-1.5 w-full bg-white p-5 rounded-2xl border border-slate-100 hover:border-teal/30 hover:shadow-md transition duration-200 ${isTextArea ? 'col-span-full' : ''}`}>
      <div className="flex justify-between items-center gap-2 mb-1">
        <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
          {label || ''}
        </label>
        <ConfidenceBadge confidence={confidence} />
      </div>
      
      <FieldInput
        type={type}
        value={value}
        onChange={onChange}
        placeholder={`Enter ${label}...`}
      />
    </div>
  );
}
