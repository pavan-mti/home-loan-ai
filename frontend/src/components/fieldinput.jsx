import React from 'react';

export default function FieldInput({ type, value, onChange, placeholder = '' }) {
  const baseClass = "w-full bg-slate-50 hover:bg-slate-100/30 border border-slate-200 focus:border-teal focus:bg-white rounded-2xl px-4 py-3 text-sm transition focus:ring-4 focus:ring-teal/15 outline-none font-medium text-slate-700";

  // Normalize type
  const normalizedType = (type || 'text').toLowerCase();

  if (normalizedType === 'long_text' || normalizedType === 'textarea') {
    return (
      <textarea
        className={`${baseClass} resize-y min-h-20`}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
      />
    );
  }

  if (normalizedType === 'number') {
    return (
      <input
        type="number"
        className={baseClass}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    );
  }

  if (normalizedType === 'date') {
    // If the value doesn't look like YYYY-MM-DD, standard <input type="date"> won't show it.
    // Let's check if the date value matches YYYY-MM-DD. If not, use type="text" so the user can see and edit the string.
    const isIsoDate = /^\d{4}-\d{2}-\d{2}$/.test(value || '');
    return (
      <input
        type={isIsoDate ? "date" : "text"}
        className={baseClass}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder || 'dd-mm-yyyy or yyyy-mm-dd'}
      />
    );
  }

  return (
    <input
      type="text"
      className={baseClass}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
    />
  );
}
