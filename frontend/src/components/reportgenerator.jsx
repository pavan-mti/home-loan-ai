"import React from 'react';

const DOCUMENT_LABELS = {
  agreement: 'Agreement',
  aos: 'AOS',
  work_order: 'Work Order',
  sale_deed: 'Sale Deed',
  other: 'Other Documents'
};

export default function ReportGenerator({ selectedTemplate, uploadedFiles, mappedData, onGenerate, loading }) {
  if (!selectedTemplate) {
    return (
      <div className=\"panel p-12 text-center border-dashed border-2 border-slate-200 bg-slate-50/50 rounded-3xl\">
        <p className=\"text-sm font-medium text-slate-500\">Please select a template and extract document values first.</p>
      </div>
    );
  }

  // Calculate statistics
  let totalFields = 0;
  let filledFields = 0;

  if (mappedData?.sections) {
    const walk = (items) => {
      for (const item of items) {
        if (item.field_type === 'group' || (item.nested_fields && item.nested_fields.length > 0)) {
          walk(item.nested_fields || []);
        } else {
          totalFields++;
          if (item.extracted_value && String(item.extracted_value).trim() !== '') {
            filledFields++;
          }
        }
      }
    };
    for (const sec of mappedData.sections) {
      walk(sec.fields || []);
    }
  }

  const uploadedKeys = Object.keys(uploadedFiles || {});

  return (
    <div className=\"space-y-6\">
      <div className=\"panel p-6 bg-white border border-slate-100 rounded-3xl shadow-sm max-w-2xl mx-auto space-y-6\">
        <h3 className=\"text-xl font-bold text-slate-800 border-b border-slate-100 pb-3\">Compilation Summary</h3>

        <div className=\"space-y-4\">
          {/* Selected Template */}
          <div className=\"flex justify-between items-center p-3 bg-slate-50 border border-slate-100 rounded-2xl\">
            <div>
              <span className=\"text-[10px] font-bold text-slate-400 uppercase tracking-wide block\">Selected Template</span>
              <span className=\"text-sm font-bold text-slate-800 mt-0.5 block\">{selectedTemplate.template_name}</span>
            </div>
<truncated 3098 bytes>