"import React, { useState, useEffect } from 'react';
import TemplateSelector from '../components/TemplateSelector';
import DocumentUploader from '../components/DocumentUploader';
import ExtractionResults from '../components/ExtractionResults';
import ReportGenerator from '../components/ReportGenerator';

export default function DocumentWorkspace({ apiRequest, token, showToast }) {
  const [activeTab, setActiveTab] = useState('template'); // template | documents | results | report
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState({});
  const [mappedData, setMappedData] = useState(null);

  const [extractionLoading, setExtractionLoading] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // Fetch templates list
  const loadTemplates = async () => {
    if (!token) return;
    try {
      const res = await apiRequest('/templates', { token });
      setTemplates(res || []);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  useEffect(() => {
    loadTemplates();
  }, [token]);

  const handleSelectTemplate = (template) => {
    setSelectedTemplate(template);
    // Reset down-stream state on template change
    setUploadedFiles({});
    setMappedData(null);
    if (template) {
      setActiveTab('documents');
    }
  };

  const handleStartExtraction = async () => {
    if (!selectedTemplate) {
      showToast('Please select a template first.', 'warning');
      return;
    }
    const fileList = Object.values(uploadedFiles);
    if (fileList.length === 0) {
      showToast('Please upload at least one document.', 'warning');
      return;
    }

    setExtractionLoading(true);
    showToast('Running text extraction and mapping...', 'info');

    try {
      const formData = new FormData();
      for (const f
<truncated 6866 bytes>