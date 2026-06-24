"import React, { useState, useEffect } from 'react';

const emptyTemplate = {
  template_key_id: '',
  template_name: '',
  template_bank: '',
  template_content_json: '{\
  \"applicant_name\": \"\",\
  \"survey_number\": \"\"\
}',
  header_template_id: '',
};

export default function ReportTemplates({ apiRequest, token, showToast }) {
  const [templates, setTemplates] = useState([]);
  const [headerTemplates, setHeaderTemplates] = useState([]);
  const [certificateText, setCertificateText] = useState('');
  const [activeTemplateSubTab, setActiveTemplateSubTab] = useState('templates'); // templates | headers | certificate

  const [templateForm, setTemplateForm] = useState(emptyTemplate);
  const [headerForm, setHeaderForm] = useState({ header_name: '', is_active: true });

  const [templateFile, setTemplateFile] = useState(null);
  const [headerFile, setHeaderFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');

  const [editingTemplateId, setEditingTemplateId] = useState(null);
  const [editingHeaderId, setEditingHeaderId] = useState(null);

  const [templateSaving, setTemplateSaving] = useState(false);
  const [headerSaving, setHeaderSaving] = useState(false);
  const [certificateSaving, setCertificateSaving] = useState(false);
  const [isEditingCertificate, setIsEditingCertificate] = useState(false);

  const [templateDragOver, setTemplateDragOver] = useState(false);
  const [headerDragOver, setHeaderDragOver] = useState(false);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!headerFile) {
      if (editingHeaderId) {
        const h = headerTemplates.find(x => x.id === editingHeaderId);
        setPreviewUrl(h ? `${API_BASE}${h.image_path}` : '');
      } else {
        setPreviewUrl('');
      }
      return;
    }

    const objectUrl = URL.createObjectURL(headerFile);
    setPreviewUrl(objectUrl);

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }
<truncated 27745 bytes>