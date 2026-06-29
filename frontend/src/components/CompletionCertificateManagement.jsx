import React, { useState, useEffect } from 'react'

const AVAILABLE_PLACEHOLDERS = [
  { code: '{{owner_name}}', label: 'Owner Name' },
  { code: '{{father_name}}', label: 'Father Name' },
  { code: '{{co_owner_name}}', label: 'Co-Owner Name' },
  { code: '{{co_owner_husband_name}}', label: 'Co-Owner Husband Name' },
  { code: '{{mobile_number}}', label: 'Mobile Number' },
  { code: '{{property_description}}', label: 'Property Description' },
  { code: '{{plot_number}}', label: 'Plot Number' },
  { code: '{{survey_number}}', label: 'Survey Number' },
  { code: '{{area_sq_yds}}', label: 'Area (Sq Yds)' },
  { code: '{{area_sq_mtrs}}', label: 'Area (Sq Mtrs)' },
  { code: '{{built_up_area}}', label: 'Built Up Area' },
  { code: '{{village}}', label: 'Village' },
  { code: '{{mandal}}', label: 'Mandal' },
  { code: '{{district}}', label: 'District' },
  { code: '{{municipality}}', label: 'Municipality' },
  { code: '{{pin_code}}', label: 'Pin Code' },
  { code: '{{inspection_date}}', label: 'Inspection Date' },
  { code: '{{date}}', label: 'Date' },
  { code: '{{bank_name}}', label: 'Bank Name' },
  { code: '{{branch_name}}', label: 'Branch Name' },
  { code: '{{city}}', label: 'City' },
]

export default function CompletionCertificateManagement({ apiRequest, token, showToast }) {
  const [certificateText, setCertificateText] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchCertificate()
  }, [])

  const fetchCertificate = async () => {
    setLoading(true)
    try {
      const data = await apiRequest('/completion-certificate', { token })
      setCertificateText(data.template_text || '')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await apiRequest('/completion-certificate', {
        method: 'PUT',
        token,
        body: { template_text: certificateText },
      })
      showToast('Completion Certificate template updated successfully.', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const insertPlaceholder = (code) => {
    setCertificateText((prev) => prev + (prev.length > 0 && !prev.endsWith(' ') && !prev.endsWith('\n') ? ' ' : '') + code)
    showToast(`Inserted ${code}`, 'info')
  }

  if (loading) {
    return (
      <div className="panel p-12 text-center text-slate-400">
        <svg className="animate-spin h-6 w-6 mx-auto mb-2 text-slate-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        Loading completion certificate template...
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Editor Panel */}
      <div className="panel p-6 flex flex-col justify-between min-h-[500px]">
        <div>
          <div className="flex justify-between items-center pb-4 border-b border-slate-100 mb-6">
            <div>
              <h3 className="font-display text-2xl font-bold text-slate-900">Completion Certificate Template</h3>
              <p className="text-xs text-slate-500 mt-1">
                Customize the boilerplate completion certificate text rendered before report tables.
              </p>
            </div>
            <button
              onClick={handleSave}
              disabled={saving}
              type="button"
              className="btn-accent px-6 py-2.5 shadow-md"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>

          <form onSubmit={handleSave}>
            <label className="text-xs font-bold text-slate-600 uppercase tracking-wider block mb-2">
              Certificate Template Text
            </label>
            <textarea
              rows={18}
              value={certificateText}
              onChange={(e) => setCertificateText(e.target.value)}
              className="w-full font-mono text-xs p-4 bg-slate-50/70 border border-slate-200 rounded-2xl focus:border-teal focus:bg-white focus:outline-none transition leading-relaxed text-slate-800"
              placeholder="Enter completion certificate template content..."
            />
          </form>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-end text-xs text-slate-400">
          <span className="font-semibold text-slate-500">{certificateText.length} characters</span>
        </div>
      </div>
    </div>
  )
}
