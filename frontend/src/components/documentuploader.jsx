"import React, { useRef, useState } from 'react';

const DOCUMENT_SLOTS = [
  { key: 'agreement', label: 'Agreement', description: 'Agreement copy document (.pdf/.docx)' },
  { key: 'aos', label: 'AOS', description: 'Agreement of Sale copy (.pdf/.docx)' },
  { key: 'work_order', label: 'Work Order', description: 'Construction work order (.pdf/.docx)' },
  { key: 'sale_deed', label: 'Sale Deed', description: 'Property registered sale deed (.pdf/.docx)' },
  { key: 'other', label: 'Other Documents', description: 'Any auxiliary layouts/permissions (.pdf/.docx/.jpg/.png)' }
];

export default function DocumentUploader({ files, onFilesChange, onStartExtraction, loading }) {
  const [dragOverKey, setDragOverKey] = useState(null);

  const handleFileChange = (key, file) => {
    onFilesChange({
      ...files,
      [key]: file
    });
  };

  const handleDrag = (e, key, state) => {
    e.preventDefault();
    e.stopPropagation();
    if (state) {
      setDragOverKey(key);
    } else {
      setDragOverKey(null);
    }
  };

  const handleDrop = (e, key) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOverKey(null);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles && droppedFiles.length > 0) {
      handleFileChange(key, droppedFiles[0]);
    }
  };

  const clearFile = (key) => {
    const nextFiles = { ...files };
    delete nextFiles[key];
    onFilesChange(nextFiles);
  };

  const fileCount = Object.keys(files).length;

  return (
    <div className=\"space-y-6\">
      <div className=\"panel p-6 bg-white border border-slate-100 rounded-3xl shadow-sm\">
        <h3 className=\"text-xl font-bold text-slate-800 mb-1\">Upload Documents</h3>
        <p className=\"text-xs text-slate-500 mb-6\">Provide the target files below. Files will be scanned and mapped to the selected template schema.</p>

        <div className=\"grid gap-4 md:grid-cols-2\">
          {DOCUMENT_SLOTS.map((slot) => {
            const file = files[slot.key
<truncated 5152 bytes>