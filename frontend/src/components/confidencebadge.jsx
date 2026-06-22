import React from 'react';

export default function ConfidenceBadge({ confidence }) {
  if (confidence === undefined || confidence === null) return null;

  // Normalize confidence to 0-100 scale
  const value = confidence <= 1.0 ? Math.round(confidence * 100) : Math.round(confidence);

  let badgeColor = 'bg-rose-50 text-rose-700 border-rose-200';
  if (value >= 90) {
    badgeColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (value >= 70) {
    badgeColor = 'bg-amber-50 text-amber-700 border-amber-200';
  }

  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-sm ${badgeColor}`}>
      {value}% Confidence
    </span>
  );
}
