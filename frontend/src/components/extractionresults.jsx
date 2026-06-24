"import React, { useState, useEffect } from 'react';
import DynamicFieldCard from './DynamicFieldCard';

export default function ExtractionResults({ mappedData, onFieldChange, onSave, onCopy }) {
  const [activeTab, setActiveTab] = useState('');

  // Set initial active section tab
  useEffect(() => {
    if (mappedData?.sections?.length > 0) {
      setActiveTab(mappedData.sections[0].name);
    }
  }, [mappedData]);

  if (!mappedData || !mappedData.sections || mappedData.sections.length === 0) {
    return (
      <div className=\"panel p-12 text-center border-dashed border-2 border-slate-200 bg-slate-50/50 rounded-3xl\">
        <p className=\"text-sm font-medium text-slate-500\">No extracted field results found. Please complete the Template and Documents stages first.</p>
      </div>
    );
  }

  const currentSection = mappedData.sections.find(s => s.name === activeTab) || mappedData.sections[0];

  const gatherFields = (fieldsList) => {
    const flat = [];
    const walk = (items) => {
      for (const item of items) {
        if (item.field_type === 'group' || (item.nested_fields && item.nested_fields.length > 0)) {
          walk(item.nested_fields || []);
        } else {
          flat.push(item);
        }
      }
    };
    walk(fieldsList || []);
    return flat;
  };

  const fieldsToRender = gatherFields(currentSection.fields);

  return (
    <div className=\"space-y-6\">
      {/* Section Tabs Selector */}
      <div className=\"border-b border-slate-200 bg-white/50 flex flex-wrap p-1.5 rounded-2xl border shadow-sm gap-1\">
        {mappedData.sections.map((section) => (
          <button
            key={section.name}
            type=\"button\"
            className={`px-4 py-2.5 text-xs font-bold rounded-xl transition ${
              activeTab === section.name
                ? 'bg-slate-900 text-white shadow-md'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
            onClick={() => setActive
<truncated 1853 bytes>