"import React, { useEffect, useState } from 'react';

export default function TemplateSelector({ templates, selectedTemplate, onSelectTemplate, apiRequest, token }) {
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedTemplate) {
      setFields([]);
      return;
    }

    setLoading(true);
    apiRequest(`/templates/${selectedTemplate.template_id}/fields`, { token })
      .then(res => {
        setFields(res.fields || []);
      })
      .catch(err => {
        console.error(\"Error fetching template fields:\", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedTemplate, apiRequest, token]);

  const handleSelect = (e) => {
    const id = parseInt(e.target.value);
    const template = templates.find(t => t.template_id === id);
    onSelectTemplate(template || null);
  };

  return (
    <div className=\"space-y-6\">
      <div className=\"panel p-6 bg-white border border-slate-100 rounded-3xl shadow-sm\">
        <h3 className=\"text-xl font-bold text-slate-800 mb-2\">Select Template</h3>
        <p className=\"text-xs text-slate-500 mb-6\">Select a standard banking valuation template to configure the extraction target schema.</p>

        <div className=\"flex flex-col gap-2\">
          <label className=\"text-xs font-bold text-slate-500 uppercase tracking-wide\">Choose Template Layout</label>
          <select
            className=\"w-full bg-slate-50 hover:bg-slate-100/30 border border-slate-200 focus:border-teal focus:bg-white rounded-2xl px-4 py-3 text-sm transition focus:ring-4 focus:ring-teal/15 outline-none font-medium text-slate-700\"
            value={selectedTemplate?.template_id || ''}
            onChange={handleSelect}
          >
            <option value=\"\">-- Choose Template --</option>
            {templates.map((tpl) => (
              <option key={tpl.template_id} value={tpl.template_id}>
                {tpl.template_name
<truncated 3111 bytes>