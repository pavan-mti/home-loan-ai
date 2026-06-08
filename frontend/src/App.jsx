import { useEffect, useMemo, useState } from 'react'
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType } from 'docx'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const emptyAuth = { username: '', password: '', confirmPassword: '' }
const emptyValuer = { valuer_name: '', valuer_contact: '', valuer_header_image_path: '' }
const emptyHlc = { hlc_name: '', hlc_contact: '', hlc_area: '', hlc_bank: '' }
const emptyTemplate = {
  template_key_id: '',
  template_name: '',
  template_bank: '',
  template_content_json: '{\n  "applicant_name": "",\n  "survey_number": ""\n}',
}

async function apiRequest(path, { method = 'GET', token, body, formData } = {}) {
  const headers = {}
  if (token) headers.Authorization = `Bearer ${token}`
  if (body && !formData) headers['Content-Type'] = 'application/json'

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: formData ? formData : body ? JSON.stringify(body) : undefined,
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || 'Request failed')
  }
  return payload
}

function useAuthState() {
  const [token, setToken] = useState(() => localStorage.getItem('hlv-token') || '')
  const [user, setUser] = useState(null)

  useEffect(() => {
    if (!token) return
    apiRequest('/auth/me', { token })
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('hlv-token')
        setToken('')
        setUser(null)
      })
  }, [token])

  const login = (nextToken, nextUser) => {
    localStorage.setItem('hlv-token', nextToken)
    setToken(nextToken)
    setUser(nextUser)
  }

  const logout = () => {
    localStorage.removeItem('hlv-token')
    setToken('')
    setUser(null)
  }

  return { token, user, login, logout }
}

function App() {
  const auth = useAuthState()
  const [mode, setMode] = useState('login')
  const [authForm, setAuthForm] = useState(emptyAuth)
  const [activeSection, setActiveSection] = useState('dashboard')
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [valuers, setValuers] = useState([])
  const [hlcRecords, setHlcRecords] = useState([])
  const [templates, setTemplates] = useState([])
  const [valuerForm, setValuerForm] = useState(emptyValuer)
  const [hlcForm, setHlcForm] = useState(emptyHlc)
  const [templateForm, setTemplateForm] = useState(emptyTemplate)
  const [templateFile, setTemplateFile] = useState(null)
  const [permissionFile, setPermissionFile] = useState(null)
  const [permissionResult, setPermissionResult] = useState(null)
  const [editingValuerId, setEditingValuerId] = useState(null)
  const [editingHlcId, setEditingHlcId] = useState(null)
  const [editingTemplateId, setEditingTemplateId] = useState(null)

  const authenticated = Boolean(auth.user && auth.token)

  const refreshCollections = async () => {
    if (!auth.token) return
    const [valuerList, hlcList, templateList] = await Promise.all([
      apiRequest('/valuers', { token: auth.token }),
      apiRequest('/hlc', { token: auth.token }),
      apiRequest('/templates', { token: auth.token }),
    ])
    setValuers(valuerList)
    setHlcRecords(hlcList)
    setTemplates(templateList)
  }

  useEffect(() => {
    if (authenticated) {
      refreshCollections().catch((err) => setError(err.message))
    }
  }, [authenticated])

  const greeting = useMemo(() => {
    if (!auth.user) return 'Cloud-first valuation workflow'
    return `Working as ${auth.user.username}`
  }, [auth.user])

  const handleAuthSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setStatus('')
    try {
      if (mode === 'register') {
        await apiRequest('/auth/register', {
          method: 'POST',
          body: {
            username: authForm.username,
            password: authForm.password,
            confirm_password: authForm.confirmPassword,
          },
        })
        setMode('login')
        setStatus('Registration complete. Log in to continue.')
        return
      }

      const payload = await apiRequest('/auth/login', {
        method: 'POST',
        body: { username: authForm.username, password: authForm.password },
      })
      auth.login(payload.token, payload.user)
      setAuthForm(emptyAuth)
      setActiveSection('dashboard')
      setStatus('Logged in successfully.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleValuerSave = async () => {
    setError('')
    try {
      if (editingValuerId) {
        await apiRequest(`/valuers/${editingValuerId}`, {
          method: 'PUT',
          token: auth.token,
          body: valuerForm,
        })
      } else {
        await apiRequest('/valuers', {
          method: 'POST',
          token: auth.token,
          body: valuerForm,
        })
      }
      setValuerForm(emptyValuer)
      setEditingValuerId(null)
      await refreshCollections()
      setStatus('Valuer saved.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleHlcSave = async () => {
    setError('')
    try {
      if (editingHlcId) {
        await apiRequest(`/hlc/${editingHlcId}`, {
          method: 'PUT',
          token: auth.token,
          body: hlcForm,
        })
      } else {
        await apiRequest('/hlc', {
          method: 'POST',
          token: auth.token,
          body: hlcForm,
        })
      }
      setHlcForm(emptyHlc)
      setEditingHlcId(null)
      await refreshCollections()
      setStatus('HLC saved.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleTemplateSave = async () => {
    setError('')
    try {
      const formData = new FormData()
      formData.append('template_key_id', templateForm.template_key_id)
      formData.append('template_name', templateForm.template_name)
      formData.append('template_bank', templateForm.template_bank)
      formData.append('template_content_json', templateForm.template_content_json)
      if (templateFile) formData.append('template_file', templateFile)

      if (editingTemplateId) {
        await apiRequest(`/templates/${editingTemplateId}`, {
          method: 'PUT',
          token: auth.token,
          body: {
            ...templateForm,
            template_content_json: JSON.parse(templateForm.template_content_json),
          },
        })
      } else {
        await apiRequest('/templates', {
          method: 'POST',
          token: auth.token,
          formData,
        })
      }

      setTemplateForm(emptyTemplate)
      setTemplateFile(null)
      setEditingTemplateId(null)
      await refreshCollections()
      setStatus('Template saved.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handlePermissionSubmit = async () => {
    setError('')
    try {
      if (!permissionFile) throw new Error('Choose a file first.')
      const formData = new FormData()
      formData.append('upload', permissionFile)
      const result = await apiRequest('/documents/permission-number', {
        method: 'POST',
        token: auth.token,
        formData,
      })
      setPermissionResult(result)
      setStatus('Permission number extracted.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDownloadPermissionResult = async () => {
    if (!permissionResult) return

    const doc = new Document({
      sections: [
        {
          properties: {},
          children: [
            new Paragraph({
              text: 'Permission Extraction Result',
              heading: HeadingLevel.TITLE,
              alignment: AlignmentType.CENTER,
            }),
            new Paragraph({ text: '' }),
            new Paragraph({ children: [new TextRun({ text: 'Permission Number: ', bold: true }), new TextRun(permissionResult.permission_number || 'Not detected')] }),
            new Paragraph({ children: [new TextRun({ text: 'Document ID: ', bold: true }), new TextRun(String(permissionResult.document_id || ''))] }),
            new Paragraph({ text: '' }),
            new Paragraph({ text: 'AI Extraction Snapshot', heading: HeadingLevel.HEADING_1 }),
            new Paragraph({ text: JSON.stringify(permissionResult.analysis, null, 2) }),
            new Paragraph({ text: '' }),
            new Paragraph({ text: 'Extracted Text Preview', heading: HeadingLevel.HEADING_1 }),
            new Paragraph({ text: permissionResult.extracted_text || '' }),
          ],
        },
      ],
    })

    const blob = await Packer.toBlob(doc)
    const objectUrl = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = `permission_result_${permissionResult.document_id || 'export'}.docx`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(objectUrl)
  }

  const handleDelete = async (path, id) => {
    setError('')
    try {
      await apiRequest(`${path}/${id}`, { method: 'DELETE', token: auth.token })
      await refreshCollections()
      setStatus('Item deleted.')
    } catch (err) {
      setError(err.message)
    }
  }

  const openEditValuer = (valuer) => {
    setValuerForm({
      valuer_name: valuer.valuer_name,
      valuer_contact: valuer.valuer_contact,
      valuer_header_image_path: valuer.valuer_header_image_path || '',
    })
    setEditingValuerId(valuer.valuer_id)
    setActiveSection('valuers')
  }

  const openEditHlc = (record) => {
    setHlcForm({
      hlc_name: record.hlc_name,
      hlc_contact: record.hlc_contact,
      hlc_area: record.hlc_area,
      hlc_bank: record.hlc_bank,
    })
    setEditingHlcId(record.hlc_id)
    setActiveSection('hlc')
  }

  const openEditTemplate = (record) => {
    setTemplateForm({
      template_key_id: record.template_key_id,
      template_name: record.template_name,
      template_bank: record.template_bank,
      template_content_json: JSON.stringify(record.template_content_json || {}, null, 2),
    })
    setEditingTemplateId(record.template_id)
    setActiveSection('templates')
  }

  if (!authenticated) {
    return (
      <div className="min-h-screen bg-hero-radial px-4 py-8 text-slate-900">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.15fr_0.85fr]">
          <section className="panel overflow-hidden p-8 md:p-12">
            <div className="inline-flex rounded-full border border-teal/15 bg-teal/10 px-4 py-2 text-xs font-bold uppercase tracking-[0.25em] text-teal">
              Home Loan Valuation AI
            </div>
            <h1 className="mt-6 max-w-2xl font-display text-5xl font-bold leading-tight md:text-7xl">
              AI-assisted valuation report automation built for real workflow pressure.
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600 md:text-lg">
              Register freelancers, manage valuers and HLC records, store templates, and extract permission numbers from PDFs, scanned files, images, and DOCX documents.
            </p>
            <div className="mt-8 grid gap-4 sm:grid-cols-3">
              {[
                ['Secure login', 'PBKDF2 password hashing and bearer sessions'],
                ['OCR ready', 'PDF, scan, image, and Word document extraction'],
                ['Cloud friendly', 'Supabase/PostgreSQL via DATABASE_URL'],
              ].map(([title, text]) => (
                <div key={title} className="rounded-3xl border border-slate-200/80 bg-white/80 p-5">
                  <div className="text-sm font-bold text-ink">{title}</div>
                  <div className="mt-2 text-sm leading-6 text-slate-600">{text}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="panel p-6 md:p-8">
            <div className="flex gap-2 rounded-2xl bg-slate-100 p-1">
              <button className={`tab flex-1 ${mode === 'login' ? 'tab-active' : 'tab-inactive'}`} onClick={() => setMode('login')}>
                Login
              </button>
              <button className={`tab flex-1 ${mode === 'register' ? 'tab-active' : 'tab-inactive'}`} onClick={() => setMode('register')}>
                Register
              </button>
            </div>

            <form className="mt-6 space-y-5" onSubmit={handleAuthSubmit}>
              <div>
                <label className="label">Username</label>
                <input className="field" value={authForm.username} onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })} />
              </div>
              <div>
                <label className="label">Password</label>
                <input className="field" type="password" value={authForm.password} onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })} />
              </div>
              {mode === 'register' && (
                <div>
                  <label className="label">Confirm Password</label>
                  <input className="field" type="password" value={authForm.confirmPassword} onChange={(event) => setAuthForm({ ...authForm, confirmPassword: event.target.value })} />
                </div>
              )}
              <button className="btn-primary w-full" type="submit">
                {mode === 'register' ? 'Register Freelancer' : 'Login'}
              </button>
            </form>

            {(status || error) && (
              <div className={`mt-5 rounded-2xl px-4 py-3 text-sm ${error ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}`}>
                {error || status}
              </div>
            )}

            <div className="mt-8 rounded-3xl bg-ink p-5 text-white">
              <div className="text-sm uppercase tracking-[0.25em] text-white/65">Workflow note</div>
              <p className="mt-3 text-sm leading-6 text-white/80">After login, you can manage valuers, HLC records, templates, and permission extraction without leaving the app.</p>
            </div>
          </section>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-hero-radial px-4 py-4 text-slate-900 md:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="panel flex flex-col gap-4 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-[0.3em] text-teal">Home Loan Valuation AI</div>
            <h2 className="mt-2 font-display text-3xl font-bold">{greeting}</h2>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-600">User ID {auth.user.user_id}</span>
            <button className="btn-secondary" onClick={() => auth.logout()} type="button">
              Logout
            </button>
          </div>
        </header>

        <div className="mt-6 grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="panel p-4">
            {[
              ['dashboard', 'Overview'],
              ['valuers', 'Valuer Registration'],
              ['hlc', 'HLC Registration'],
              ['templates', 'Template Management'],
              ['permission', 'Permission Extraction'],
            ].map(([key, label]) => (
              <button
                key={key}
                className={`mb-2 block w-full rounded-2xl px-4 py-3 text-left text-sm font-semibold transition ${activeSection === key ? 'bg-ink text-white' : 'bg-white text-slate-600 hover:bg-slate-50'}`}
                onClick={() => setActiveSection(key)}
                type="button"
              >
                {label}
              </button>
            ))}

            <div className="mt-4 rounded-3xl bg-slate-900 p-4 text-white">
              <div className="text-xs uppercase tracking-[0.25em] text-white/60">Verification links</div>
              <div className="mt-3 space-y-3 text-sm">
                <a className="block rounded-2xl bg-white/10 px-4 py-3 hover:bg-white/15" href="https://dpms.ghmc.telangana.gov.in/AutoDCR.Common2/CitizenSearch/publicsearch.aspx?sName=GHMC&edFlag=0&iVal=1" target="_blank" rel="noreferrer">
                  GHMC Public Search
                </a>
                <a className="block rounded-2xl bg-white/10 px-4 py-3 hover:bg-white/15" href="https://app.buildnow.telangana.gov.in/login" target="_blank" rel="noreferrer">
                  Telangana BuildNow
                </a>
              </div>
            </div>
          </aside>

          <main className="space-y-6">
            {activeSection === 'dashboard' && (
              <section className="space-y-6">
                <div className="grid gap-6 lg:grid-cols-3">
                  {[
                    ['Freelancers', 'Password-protected access with token sessions.'],
                    ['OCR pipeline', 'Permission extraction from PDFs, scans, and images.'],
                    ['Templates', 'Store key-value mappings per bank template.'],
                  ].map(([title, text]) => (
                    <div key={title} className="panel p-6">
                      <div className="text-sm font-bold uppercase tracking-[0.2em] text-gold">{title}</div>
                      <p className="mt-4 text-sm leading-6 text-slate-600">{text}</p>
                    </div>
                  ))}
                </div>

                <div className="panel flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between">
                  <div>
                    <div className="text-sm font-bold uppercase tracking-[0.2em] text-teal">Document upload</div>
                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      Upload PDF, scanned PDF, DOCX, JPG, or PNG documents to extract the permission number and other key fields.
                    </p>
                  </div>
                  <button className="btn-primary" onClick={() => setActiveSection('permission')} type="button">
                    Upload Document
                  </button>
                </div>
              </section>
            )}

            {activeSection === 'valuers' && (
              <section className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
                <div className="panel p-6">
                  <h3 className="font-display text-3xl font-bold">Register Valuer</h3>
                  <div className="mt-6 space-y-5">
                    <div>
                      <label className="label">Valuer Name</label>
                      <input className="field" value={valuerForm.valuer_name} onChange={(event) => setValuerForm({ ...valuerForm, valuer_name: event.target.value })} />
                    </div>
                    <div>
                      <label className="label">Valuer Contact Number</label>
                      <input className="field" value={valuerForm.valuer_contact} onChange={(event) => setValuerForm({ ...valuerForm, valuer_contact: event.target.value })} />
                    </div>
                    <div>
                      <label className="label">Valuer Header Image Path</label>
                      <input className="field" value={valuerForm.valuer_header_image_path} onChange={(event) => setValuerForm({ ...valuerForm, valuer_header_image_path: event.target.value })} placeholder="/storage/uploads/..." />
                    </div>
                    <div className="flex gap-3">
                      <button className="btn-primary" onClick={handleValuerSave} type="button">{editingValuerId ? 'Update' : 'Save'}</button>
                      <button className="btn-secondary" onClick={() => { setValuerForm(emptyValuer); setEditingValuerId(null) }} type="button">Clear</button>
                    </div>
                  </div>
                </div>
                <div className="panel p-6">
                  <h4 className="font-display text-2xl font-bold">Saved Valuers</h4>
                  <div className="mt-5 space-y-4">
                    {valuers.length === 0 ? <p className="text-sm text-slate-500">No valuers yet.</p> : valuers.map((valuer) => (
                      <div key={valuer.valuer_id} className="rounded-3xl border border-slate-200 bg-white p-4">
                        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                          <div>
                            <div className="font-semibold text-ink">{valuer.valuer_name}</div>
                            <div className="text-sm text-slate-500">{valuer.valuer_contact}</div>
                          </div>
                          <div className="flex gap-2">
                            <button className="btn-secondary px-4 py-2" onClick={() => openEditValuer(valuer)} type="button">Edit</button>
                            <button className="btn-secondary px-4 py-2" onClick={() => handleDelete('/valuers', valuer.valuer_id)} type="button">Delete</button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {activeSection === 'hlc' && (
              <section className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
                <div className="panel p-6">
                  <h3 className="font-display text-3xl font-bold">Register HLC</h3>
                  <div className="mt-6 space-y-5">
                    <div><label className="label">HLC Name</label><input className="field" value={hlcForm.hlc_name} onChange={(event) => setHlcForm({ ...hlcForm, hlc_name: event.target.value })} /></div>
                    <div><label className="label">HLC Contact Number</label><input className="field" value={hlcForm.hlc_contact} onChange={(event) => setHlcForm({ ...hlcForm, hlc_contact: event.target.value })} /></div>
                    <div><label className="label">HLC Area</label><input className="field" value={hlcForm.hlc_area} onChange={(event) => setHlcForm({ ...hlcForm, hlc_area: event.target.value })} /></div>
                    <div><label className="label">HLC Bank</label><input className="field" value={hlcForm.hlc_bank} onChange={(event) => setHlcForm({ ...hlcForm, hlc_bank: event.target.value })} /></div>
                    <div className="flex gap-3">
                      <button className="btn-primary" onClick={handleHlcSave} type="button">{editingHlcId ? 'Update' : 'Save'}</button>
                      <button className="btn-secondary" onClick={() => { setHlcForm(emptyHlc); setEditingHlcId(null) }} type="button">Clear</button>
                    </div>
                  </div>
                </div>
                <div className="panel p-6">
                  <h4 className="font-display text-2xl font-bold">Saved HLC Records</h4>
                  <div className="mt-5 space-y-4">
                    {hlcRecords.length === 0 ? <p className="text-sm text-slate-500">No HLC records yet.</p> : hlcRecords.map((record) => (
                      <div key={record.hlc_id} className="rounded-3xl border border-slate-200 bg-white p-4">
                        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                          <div>
                            <div className="font-semibold text-ink">{record.hlc_name}</div>
                            <div className="text-sm text-slate-500">{record.hlc_area} · {record.hlc_bank}</div>
                          </div>
                          <div className="flex gap-2">
                            <button className="btn-secondary px-4 py-2" onClick={() => openEditHlc(record)} type="button">Edit</button>
                            <button className="btn-secondary px-4 py-2" onClick={() => handleDelete('/hlc', record.hlc_id)} type="button">Delete</button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {activeSection === 'templates' && (
              <section className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
                <div className="panel p-6">
                  <h3 className="font-display text-3xl font-bold">Store Template</h3>
                  <div className="mt-6 space-y-5">
                    <div><label className="label">Template Key ID</label><input className="field" value={templateForm.template_key_id} onChange={(event) => setTemplateForm({ ...templateForm, template_key_id: event.target.value })} /></div>
                    <div><label className="label">Template Name</label><input className="field" value={templateForm.template_name} onChange={(event) => setTemplateForm({ ...templateForm, template_name: event.target.value })} /></div>
                    <div><label className="label">Template Bank</label><input className="field" value={templateForm.template_bank} onChange={(event) => setTemplateForm({ ...templateForm, template_bank: event.target.value })} /></div>
                    <div><label className="label">Template Content JSON</label><textarea className="field min-h-44 font-mono text-xs" value={templateForm.template_content_json} onChange={(event) => setTemplateForm({ ...templateForm, template_content_json: event.target.value })} /></div>
                    <div><label className="label">Upload DOCX or PDF</label><input className="field p-2" type="file" accept=".docx,.pdf" onChange={(event) => setTemplateFile(event.target.files?.[0] || null)} /></div>
                    <div className="flex gap-3">
                      <button className="btn-primary" onClick={handleTemplateSave} type="button">{editingTemplateId ? 'Update Template' : 'Save Template'}</button>
                      <button className="btn-secondary" onClick={() => { setTemplateForm(emptyTemplate); setTemplateFile(null); setEditingTemplateId(null) }} type="button">Clear</button>
                    </div>
                  </div>
                </div>
                <div className="panel p-6">
                  <h4 className="font-display text-2xl font-bold">Templates and Preview</h4>
                  <div className="mt-5 space-y-4">
                    {templates.length === 0 ? <p className="text-sm text-slate-500">No templates saved yet.</p> : templates.map((record) => (
                      <div key={record.template_id} className="rounded-3xl border border-slate-200 bg-white p-4">
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                          <div>
                            <div className="font-semibold text-ink">{record.template_name}</div>
                            <div className="text-sm text-slate-500">{record.template_key_id} · {record.template_bank}</div>
                            {record.template_preview_text && <p className="mt-3 max-h-28 overflow-hidden text-sm text-slate-600">{record.template_preview_text}</p>}
                          </div>
                          <div className="flex gap-2">
                            <button className="btn-secondary px-4 py-2" onClick={() => openEditTemplate(record)} type="button">Edit</button>
                            <button className="btn-secondary px-4 py-2" onClick={() => handleDelete('/templates', record.template_id)} type="button">Delete</button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </section>
            )}

            {activeSection === 'permission' && (
              <section className="grid gap-6 xl:grid-cols-[420px_minmax(0,1fr)]">
                <div className="panel p-6">
                  <h3 className="font-display text-3xl font-bold">Get Permission Number</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-600">Upload a PDF, scanned PDF, image, or Word document. The backend will OCR and search for permission keywords.</p>
                  <div className="mt-6 space-y-5">
                    <div><label className="label">Upload Document</label><input className="field p-2" type="file" accept=".pdf,.docx,.jpg,.jpeg,.png,.webp,.tif,.tiff" onChange={(event) => setPermissionFile(event.target.files?.[0] || null)} /></div>
                    <div className="flex gap-3">
                      <button className="btn-primary" onClick={handlePermissionSubmit} type="button">Extract Permission Number</button>
                      <button className="btn-secondary" onClick={() => { setPermissionFile(null); setPermissionResult(null) }} type="button">Clear</button>
                    </div>
                    <button className="btn-secondary w-full" onClick={() => setPermissionFile(null)} type="button">Upload New Document</button>
                  </div>
                </div>
                <div className="panel p-6">
                  <h4 className="font-display text-2xl font-bold">Result</h4>
                  {permissionResult ? (
                    <div className="mt-5 space-y-4">
                      <div className="rounded-3xl bg-ink p-5 text-white">
                        <div className="text-xs uppercase tracking-[0.25em] text-white/60">Permission Number</div>
                        <div className="mt-3 text-2xl font-bold">{permissionResult.permission_number || 'Not detected'}</div>
                      </div>
                      <div className="flex gap-3">
                        <button className="btn-primary" onClick={() => navigator.clipboard.writeText(permissionResult.permission_number || '')} type="button">Copy Permission Number</button>
                        <button className="btn-secondary" onClick={handleDownloadPermissionResult} type="button">Download Result</button>
                      </div>
                      <div className="rounded-3xl border border-slate-200 bg-white p-4">
                        <div className="text-sm font-bold text-slate-700">AI Extraction Snapshot</div>
                        <pre className="mt-3 max-h-72 overflow-auto text-xs leading-6 text-slate-600">{JSON.stringify(permissionResult.analysis, null, 2)}</pre>
                      </div>
                      <div className="rounded-3xl border border-slate-200 bg-white p-4">
                        <div className="text-sm font-bold text-slate-700">Extracted Text Preview</div>
                        <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap text-xs leading-6 text-slate-600">{permissionResult.extracted_text}</pre>
                      </div>
                    </div>
                  ) : (
                    <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-white/70 p-10 text-center text-sm text-slate-500">
                      No document processed yet.
                    </div>
                  )}
                  <div className="mt-6 grid gap-3 md:grid-cols-2">
                    <a className="btn-secondary" href="https://dpms.ghmc.telangana.gov.in/AutoDCR.Common2/CitizenSearch/publicsearch.aspx?sName=GHMC&edFlag=0&iVal=1" target="_blank" rel="noreferrer">GHMC Public Search</a>
                    <a className="btn-secondary" href="https://app.buildnow.telangana.gov.in/login" target="_blank" rel="noreferrer">Telangana BuildNow Portal</a>
                  </div>
                </div>
              </section>
            )}
          </main>
        </div>

        {(status || error) && (
          <div className={`mt-6 rounded-2xl px-4 py-3 text-sm ${error ? 'bg-rose-50 text-rose-700' : 'bg-emerald-50 text-emerald-700'}`}>
            {error || status}
          </div>
        )}
      </div>
    </div>
  )
}

export default App