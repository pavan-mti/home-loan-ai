import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export default function HeaderManagement({ apiRequest, token, showToast }) {
  const [headers, setHeaders] = useState([])
  const [loading, setLoading] = useState(false)

  // Form states
  const [headerName, setHeaderName] = useState('')
  const [displayOrder, setDisplayOrder] = useState(0)
  const [isActive, setIsActive] = useState(true)
  const [isDefault, setIsDefault] = useState(false)
  const [headerFile, setHeaderFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [editingHeaderId, setEditingHeaderId] = useState(null)
  const [saving, setSaving] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const fetchHeaders = async () => {
    if (!token) return
    setLoading(true)
    try {
      const data = await apiRequest('/header-templates', { token })
      setHeaders(data)
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHeaders()
  }, [token])

  useEffect(() => {
    if (!headerFile) {
      if (editingHeaderId) {
        const h = headers.find(x => x.id === editingHeaderId)
        setPreviewUrl(h ? `${API_BASE}${h.image_path}` : '')
      } else {
        setPreviewUrl('')
      }
      return
    }

    const objectUrl = URL.createObjectURL(headerFile)
    setPreviewUrl(objectUrl)

    return () => {
      URL.revokeObjectURL(objectUrl)
    }
  }, [headerFile, editingHeaderId, headers])

  const resetForm = () => {
    setHeaderName('')
    setDisplayOrder(0)
    setIsActive(true)
    setIsDefault(false)
    setHeaderFile(null)
    setPreviewUrl('')
    setEditingHeaderId(null)
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragOver(true)
    } else if (e.type === 'dragleave') {
      setDragOver(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragOver(false)
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const file = files[0]
      const ext = file.name.split('.').pop().toLowerCase()
      if (['png', 'jpg', 'jpeg'].includes(ext)) {
        setHeaderFile(file)
        showToast(`Loaded image ${file.name}`, 'info')
      } else {
        showToast('Only PNG, JPG, and JPEG formats are supported.', 'warning')
      }
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!headerName.trim()) {
      showToast('Please enter a header letterhead name.', 'warning')
      return
    }
    if (!editingHeaderId && !headerFile) {
      showToast('Please select or drop a letterhead image file.', 'warning')
      return
    }

    setSaving(true)
    try {
      const formData = new FormData()
      formData.append('header_name', headerName)
      formData.append('display_order', displayOrder)
      formData.append('is_active', isActive)
      formData.append('is_default', isDefault)
      if (headerFile) {
        formData.append('file', headerFile)
      }

      if (editingHeaderId) {
        await apiRequest(`/header-templates/${editingHeaderId}`, {
          method: 'PUT',
          token,
          formData,
        })
        showToast('Header letterhead updated successfully.', 'success')
      } else {
        await apiRequest('/header-templates', {
          method: 'POST',
          token,
          formData,
        })
        showToast('New header letterhead registered.', 'success')
      }

      resetForm()
      await fetchHeaders()
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const openEdit = (header) => {
    setEditingHeaderId(header.id)
    setHeaderName(header.header_name)
    setDisplayOrder(header.display_order || 0)
    setIsActive(header.is_active)
    setIsDefault(header.is_default)
    setHeaderFile(null)
    setPreviewUrl(`${API_BASE}${header.image_path}`)
  }

  const handleToggleActive = async (header) => {
    try {
      const formData = new FormData()
      formData.append('is_active', !header.is_active)
      await apiRequest(`/header-templates/${header.id}`, {
        method: 'PUT',
        token,
        formData,
      })
      showToast(`Header ${!header.is_active ? 'enabled' : 'disabled'}.`, 'info')
      await fetchHeaders()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleSetDefault = async (headerId) => {
    try {
      await apiRequest(`/header-templates/${headerId}/set-default`, {
        method: 'PUT',
        token,
      })
      showToast('Default header updated.', 'success')
      await fetchHeaders()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleDelete = async (headerId) => {
    if (!window.confirm('Are you sure you want to delete this header letterhead?')) return
    try {
      await apiRequest(`/header-templates/${headerId}`, {
        method: 'DELETE',
        token,
      })
      showToast('Header deleted successfully.', 'success')
      if (editingHeaderId === headerId) resetForm()
      await fetchHeaders()
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
      {/* Header Upload/Edit Form Panel */}
      <div className="panel p-6 h-fit">
        <h3 className="font-display text-2xl font-bold text-slate-900 mb-1">
          {editingHeaderId ? 'Edit Valuer Header' : 'Add Header Letterhead'}
        </h3>
        <p className="text-xs text-slate-500 mb-6">
          Upload letterhead banner graphics to apply automatically to report outputs.
        </p>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="text-xs font-bold text-slate-600 uppercase tracking-wider block mb-1">Header Name</label>
            <input
              type="text"
              className="w-full bg-slate-50 hover:bg-slate-100/50 border border-slate-200 focus:border-teal focus:bg-white rounded-2xl px-4 py-2.5 text-sm transition font-medium text-slate-700 outline-none"
              placeholder="e.g. State Bank Main Letterhead"
              value={headerName}
              onChange={(e) => setHeaderName(e.target.value)}
            />
          </div>



          {/* Drag & Drop Zone */}
          <div>
            <label className="text-xs font-bold text-slate-600 uppercase tracking-wider block mb-1">
              {editingHeaderId ? 'Replace Image (Optional)' : 'Letterhead Graphic (.png, .jpg)'}
            </label>
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-2xl p-6 text-center transition ${dragOver ? 'border-teal bg-teal/5' : 'border-slate-200 hover:border-slate-300 bg-white'}`}
            >
              <input
                id="header-upload-input"
                type="file"
                accept=".png,.jpg,.jpeg"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    setHeaderFile(e.target.files[0])
                  }
                }}
              />
              <label htmlFor="header-upload-input" className="cursor-pointer flex flex-col items-center">
                <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <span className="text-xs font-bold text-slate-700">Click or drag banner image</span>
                <span className="text-[10px] text-slate-400 mt-1">PNG, JPG, JPEG up to 5MB</span>
              </label>
            </div>
          </div>

          {/* Preview Panel */}
          {previewUrl && (
            <div className="p-3 bg-slate-50 border border-slate-200/60 rounded-2xl animate-fade-in">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">Image Preview</span>
              <div className="bg-white rounded-xl border border-slate-100 p-2 overflow-hidden flex items-center justify-center min-h-[80px] max-h-[140px]">
                <img src={previewUrl} alt="Preview" className="max-h-[120px] w-auto object-contain" />
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="btn-primary flex-1 py-2.5 text-xs font-bold"
            >
              {saving ? 'Saving...' : editingHeaderId ? 'Update Header' : 'Save Header'}
            </button>
            {editingHeaderId && (
              <button
                type="button"
                onClick={resetForm}
                className="btn-secondary py-2.5 text-xs font-bold"
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Saved Headers Library Grid Panel */}
      <div className="panel p-6 flex flex-col min-h-[400px]">
        <div className="flex justify-between items-center pb-4 border-b border-slate-100 shrink-0">
          <div>
            <h3 className="font-display text-2xl font-bold text-slate-900">Header Library</h3>
            <p className="text-xs text-slate-500">Manage registered valuer letterheads and default selections.</p>
          </div>
          <span className="text-xs font-bold text-slate-400 bg-slate-100 px-3 py-1 rounded-full">
            {headers.length} Assets
          </span>
        </div>

        <div className="flex-1 overflow-y-auto mt-4 pr-1">
          {loading && headers.length === 0 ? (
            <div className="text-center py-12 text-xs text-slate-400 font-medium">Loading headers...</div>
          ) : headers.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
              <p className="text-sm text-slate-500 font-medium">No headers registered yet.</p>
            </div>
          ) : (
            <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
              {headers.map((h) => (
                <div
                  key={h.id}
                  className={`rounded-2xl border p-4 flex flex-col justify-between transition-all duration-200 bg-white ${h.is_default ? 'border-amber-300 shadow-md shadow-amber-500/5 ring-2 ring-amber-400/20' : 'border-slate-200 hover:border-slate-300'}`}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div>
                        <h4 className="font-bold text-slate-800 text-sm">{h.header_name}</h4>
                        {h.image_width && h.image_height && (
                          <span className="text-[10px] font-mono text-slate-400">
                            {h.image_width} × {h.image_height} px
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {h.is_default && (
                          <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full shadow-xs">
                            ⭐ Default Header
                          </span>
                        )}
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${h.is_active ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
                          {h.is_active ? 'Active' : 'Disabled'}
                        </span>
                      </div>
                    </div>

                    {/* Thumbnail banner preview */}
                    <div className="bg-slate-50 rounded-xl border border-slate-100 p-2 overflow-hidden flex items-center justify-center min-h-[90px] max-h-[120px] mb-4">
                      <img src={`${API_BASE}${h.image_path}`} alt={h.header_name} className="max-h-[100px] w-auto object-contain" />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                    <button
                      type="button"
                      onClick={() => handleToggleActive(h)}
                      className="text-slate-600 hover:text-slate-900 font-semibold text-xs"
                    >
                      {h.is_active ? 'Disable' : 'Enable'}
                    </button>

                    <div className="flex items-center gap-2">
                      {!h.is_default && (
                        <button
                          type="button"
                          onClick={() => handleSetDefault(h.id)}
                          className="text-amber-600 hover:text-amber-800 font-bold text-xs bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200/60"
                        >
                          Make Default
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => openEdit(h)}
                        className="text-slate-700 hover:text-slate-900 font-semibold px-2 py-1 bg-slate-100 rounded-lg"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(h.id)}
                        className="text-rose-600 hover:text-rose-800 font-semibold px-2 py-1 hover:bg-rose-50 rounded-lg"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
