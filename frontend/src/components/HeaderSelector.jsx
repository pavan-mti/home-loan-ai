import React, { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export default function HeaderSelector({ apiRequest, token, selectedHeaderId, setSelectedHeaderId, showToast }) {
  const [headers, setHeaders] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) return
    setLoading(true)
    apiRequest('/header-templates', { token })
      .then((data) => {
        const activeHeaders = data.filter(h => h.is_active)
        setHeaders(activeHeaders)
        
        // Auto-select default header if nothing selected yet
        if (!selectedHeaderId && activeHeaders.length > 0) {
          const defaultHeader = activeHeaders.find(h => h.is_default) || activeHeaders[0]
          if (defaultHeader) {
            setSelectedHeaderId(defaultHeader.id)
          }
        }
      })
      .catch((err) => {
        if (showToast) showToast(err.message, 'error')
      })
      .finally(() => setLoading(false))
  }, [token])

  if (loading && headers.length === 0) {
    return <div className="text-xs text-slate-400 py-3">Loading letterhead options...</div>
  }

  if (headers.length === 0) {
    return (
      <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
        No active header letterheads available in library. Standard template layout will be used.
      </div>
    )
  }

  return (
    <div className="space-y-3 text-left max-w-xl mx-auto my-6">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
          Select Valuer Letterhead Banner
        </label>
        <span className="text-[11px] text-slate-400">
          Applied at top of report output
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {headers.map((h) => {
          const isSelected = selectedHeaderId === h.id
          return (
            <div
              key={h.id}
              onClick={() => setSelectedHeaderId(h.id)}
              className={`cursor-pointer rounded-2xl border p-3.5 transition duration-200 bg-white flex flex-col justify-between ${isSelected ? 'border-teal ring-2 ring-teal/20 bg-teal/5 shadow-sm' : 'border-slate-200 hover:border-slate-300'}`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${isSelected ? 'border-teal bg-teal text-white' : 'border-slate-300'}`}>
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </div>
                  <span className="text-xs font-bold text-slate-800 truncate">{h.header_name}</span>
                </div>
                {h.is_default && (
                  <span className="text-[9px] font-extrabold bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full shrink-0">
                    ⭐ Default
                  </span>
                )}
              </div>

              <div className="bg-slate-50 rounded-xl border border-slate-100 p-1.5 overflow-hidden flex items-center justify-center h-14">
                <img src={`${API_BASE}${h.image_path}`} alt={h.header_name} className="max-h-12 w-auto object-contain" />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
