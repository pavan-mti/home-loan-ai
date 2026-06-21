import { useEffect, useMemo, useState } from 'react'
import { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType } from 'docx'

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

const FRIENDLY_NAMES = {
  applicant_name: "Applicant Name",
  owner_name: "Owner Name",
  property_address: "Property Address",
  document_number: "Document Number",
  registration_details: "Registration Details",
  survey_number: "Survey Number",
  plot_number: "Plot Number",
  door_number: "Door Number",
  village: "Village",
  mandal: "Mandal",
  district: "District",
  market_value: "Market Value",
  guideline_value: "Guideline Value",
  legal_disputes: "Legal Disputes",
  is_disputed: "Is Disputed",
  built_up_area: "Built Up Area",
  land_area: "Land Area",
  built_up_area_sqft: "Built Up Area (Sq. Ft.)",
  land_area_sqyd: "Land Area (Sq. Yd.)",
  property_description: "Property Description",
  permission_number: "Permission Number",

  // Section 1: General
  valuation_purpose: "Valuation Purpose",
  inspection_date: "Inspection Date",
  valuation_date: "Valuation Date",

  // Section 3: Documents
  aos_buyer_name: "AOS Buyer Name",
  aos_seller_name: "AOS Seller Name",
  aos_sale_deed_doc_number: "AOS Sale Deed Doc Number",
  aos_property_schedule: "AOS Property Schedule",
  wo_party_name: "Work Order Contractor Name",
  rera_registration_number: "RERA Registration Number",

  // Section 4: Ownership
  purchaser_name: "Purchaser Name",
  purchaser_address: "Purchaser Address",
  purchaser_phone: "Purchaser Phone Number",
  ownership_type: "Ownership Type",

  // Section 5: Property Description
  property_tenure: "Property Tenure",

  // Section 6: Prohibited
  prohibited_property_details: "Prohibited Property Details",

  // Section 7: Legal
  legal_opinion: "Legal Opinion",

  // Section 8: Financial
  mortgage_details: "Mortgage Details",
  ftl_buffer_zone_details: "FTL Buffer Zone Details",

  // Section 9: Location
  ts_number: "T.S. Number",
  ward: "Ward",
  taluka: "Taluka",
  layout_approval_date: "Layout Approval Date",
  layout_approval_validity: "Layout Approval Validity",
  approved_plan_authority: "Approved Plan Authority",
  approved_plan_verified: "Approved Plan Verified",
  approved_plan_comments: "Approved Plan Comments",

  // Section 11: Area Type
  city: "City / Town",
  is_residential_area: "Is Residential Area",
  is_commercial_area: "Is Commercial Area",
  is_industrial_area: "Is Industrial Area",

  // Section 12: Classification
  area_class: "Area Classification (High/Middle/Poor)",
  area_type: "Area Type (Urban/Semi Urban/Rural)",

  // Section 13: Municipality
  municipality_type: "Municipality Type",

  // Section 14: Govt Enactments
  under_govt_enactment: "Under Govt Enactment",
  enactment_details: "Enactment Details",

  // Section 15: Boundaries
  boundary_north_deed: "Boundary North (As Per Deed)",
  boundary_south_deed: "Boundary South (As Per Deed)",
  boundary_east_deed: "Boundary East (As Per Deed)",
  boundary_west_deed: "Boundary West (As Per Deed)",
  boundary_north_actual: "Boundary North (As Per Actuals)",
  boundary_south_actual: "Boundary South (As Per Actuals)",
  boundary_east_actual: "Boundary East (As Per Actuals)",
  boundary_west_actual: "Boundary West (As Per Actuals)",

  // Extras
  state: "State",
  pincode: "Pincode",
  project_name: "Project Name",
  registration_number: "Registration Number",
  registration_date: "Registration Date",
  agreement_value: "Agreement Value"
}

const UI_FIELDS_ORDER = [
  { key: 'inspection_date', label: '1. Date of inspection' },
  { key: 'valuation_date', label: '2. Date of valuation' },
  { key: 'owner_name', label: '3. Name of the Owner(s)' },
  { key: 'purchaser_details', label: '4. Name of the purchaser(s) and his / their address(es) with Phone no. (details of share of each owner in case of joint ownership)', isTextArea: true },
  { key: 'property_description', label: '5. Brief description of the property (Including leasehold / freehold etc.)', isTextArea: true },
  { key: 'prohibited_property_details', label: '6. Prohibited Properties Details', isTextArea: true },
  { key: 'legal_opinion', label: '7. Legal Opinion', isTextArea: true },
  { key: 'mortgage_details', label: '8. Mortgage Details', isTextArea: true },
  { key: 'ftl_buffer_zone_details', label: '9. FTL and Buffer Zone Details', isTextArea: true },
  { key: 'plot_survey_number', label: 'Plot No. / Survey No.' },
  { key: 'door_house_number', label: 'Door No / House No' },
  { key: 'ts_number_village', label: 'T.S. No. / Village' },
  { key: 'ward_taluka', label: 'Ward / Taluka' },
  { key: 'mandal_district', label: 'Mandal / District' },
  { key: 'property_address', label: '11. Postal address of the property', isTextArea: true }
]

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
  const [activeSection, setActiveSection] = useState('templates')
  const [valuers, setValuers] = useState([])
  const [hlcRecords, setHlcRecords] = useState([])
  const [templates, setTemplates] = useState([])
  const [valuerForm, setValuerForm] = useState(emptyValuer)
  const [hlcForm, setHlcForm] = useState(emptyHlc)
  const [templateForm, setTemplateForm] = useState(emptyTemplate)
  
  // Drag & drop file states
  const [templateFile, setTemplateFile] = useState(null)
  const [permissionFile, setPermissionFile] = useState(null)
  const [reportFiles, setReportFiles] = useState([])
  const [permissionDragOver, setPermissionDragOver] = useState(false)
  const [templateDragOver, setTemplateDragOver] = useState(false)
  const [reportDragOver, setReportDragOver] = useState(false)
  
  // OCR & Loading states
  const [permissionResult, setPermissionResult] = useState(null)
  const [editingAnalysis, setEditingAnalysis] = useState(null)
  
  const [permissionLoading, setPermissionLoading] = useState(false)
  const [templateSaving, setTemplateSaving] = useState(false)
  const [valuerSaving, setValuerSaving] = useState(false)
  const [hlcSaving, setHlcSaving] = useState(false)
  const [reportLoading, setReportLoading] = useState(false)
  
  // Editing IDs
  const [editingValuerId, setEditingValuerId] = useState(null)
  const [editingHlcId, setEditingHlcId] = useState(null)
  const [editingTemplateId, setEditingTemplateId] = useState(null)
  const [selectedTemplateId, setSelectedTemplateId] = useState(null)
  
  // Sidebar state
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false)

  // Template Field Mapping Review States
  const [mappedData, setMappedData] = useState(null)
  const [editingMappedFields, setEditingMappedFields] = useState({})
  const [mappingReviewLoading, setMappingReviewLoading] = useState(false)
  const [activeReviewSectionTab, setActiveReviewSectionTab] = useState('')

  // Floating Toast Notifications System
  const [toasts, setToasts] = useState([])
  const showToast = (message, type = 'info') => {
    const id = Date.now()
    setToasts((prev) => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }

  const authenticated = Boolean(auth.user && auth.token)

  const refreshCollections = async () => {
    if (!auth.token) return
    try {
      const [valuerList, hlcList, templateList] = await Promise.all([
        apiRequest('/valuers', { token: auth.token }),
        apiRequest('/hlc', { token: auth.token }),
        apiRequest('/templates', { token: auth.token }),
      ])
      setValuers(valuerList)
      setHlcRecords(hlcList)
      setTemplates(templateList)
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  useEffect(() => {
    if (authenticated) {
      refreshCollections()
    }
  }, [authenticated])

  useEffect(() => {
    setMappedData(null)
    setEditingMappedFields({})
  }, [selectedTemplateId])

  const greeting = useMemo(() => {
    if (!auth.user) return 'Valuation Intelligence Hub'
    return `Welcome, ${auth.user.username}`
  }, [auth.user])

  const handleAuthSubmit = async (event) => {
    event.preventDefault()
    if (!authForm.username || !authForm.password) {
      showToast('Please enter both username and password.', 'warning')
      return
    }
    try {
      if (mode === 'register') {
        if (authForm.password !== authForm.confirmPassword) {
          showToast('Passwords do not match.', 'warning')
          return
        }
        await apiRequest('/auth/register', {
          method: 'POST',
          body: {
            username: authForm.username,
            password: authForm.password,
            confirm_password: authForm.confirmPassword,
          },
        })
        setMode('login')
        showToast('Registration complete. You can now log in.', 'success')
        return
      }

      const payload = await apiRequest('/auth/login', {
        method: 'POST',
        body: { username: authForm.username, password: authForm.password },
      })
      auth.login(payload.token, payload.user)
      setAuthForm(emptyAuth)
      setActiveSection('templates')
      showToast('Successfully logged in!', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleValuerSave = async () => {
    if (!valuerForm.valuer_name || !valuerForm.valuer_contact) {
      showToast('Please provide Valuer Name and Contact Number.', 'warning')
      return
    }
    setValuerSaving(true)
    try {
      if (editingValuerId) {
        await apiRequest(`/valuers/${editingValuerId}`, {
          method: 'PUT',
          token: auth.token,
          body: valuerForm,
        })
        showToast('Valuer updated successfully.', 'success')
      } else {
        await apiRequest('/valuers', {
          method: 'POST',
          token: auth.token,
          body: valuerForm,
        })
        showToast('New valuer registered successfully.', 'success')
      }
      setValuerForm(emptyValuer)
      setEditingValuerId(null)
      await refreshCollections()
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setValuerSaving(false)
    }
  }

  const handleHlcSave = async () => {
    if (!hlcForm.hlc_name || !hlcForm.hlc_contact || !hlcForm.hlc_bank) {
      showToast('Please fill out all required HLC fields.', 'warning')
      return
    }
    setHlcSaving(true)
    try {
      if (editingHlcId) {
        await apiRequest(`/hlc/${editingHlcId}`, {
          method: 'PUT',
          token: auth.token,
          body: hlcForm,
        })
        showToast('HLC updated successfully.', 'success')
      } else {
        await apiRequest('/hlc', {
          method: 'POST',
          token: auth.token,
          body: hlcForm,
        })
        showToast('HLC registered successfully.', 'success')
      }
      setHlcForm(emptyHlc)
      setEditingHlcId(null)
      await refreshCollections()
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setHlcSaving(false)
    }
  }

  const handleTemplateSave = async () => {
    if (!templateForm.template_key_id || !templateForm.template_name || !templateForm.template_bank) {
      showToast('Please fill out all required template metadata.', 'warning')
      return
    }
    setTemplateSaving(true)
    try {
      let parsedJson
      try {
        parsedJson = JSON.parse(templateForm.template_content_json)
      } catch {
        showToast('Template Content JSON is not valid JSON.', 'error')
        setTemplateSaving(false)
        return
      }

      if (editingTemplateId) {
        await apiRequest(`/templates/${editingTemplateId}`, {
          method: 'PUT',
          token: auth.token,
          body: {
            ...templateForm,
            template_content_json: parsedJson,
          },
        })
        showToast('Template metadata updated.', 'success')
      } else {
        const formData = new FormData()
        formData.append('template_key_id', templateForm.template_key_id)
        formData.append('template_name', templateForm.template_name)
        formData.append('template_bank', templateForm.template_bank)
        if (!templateFile) {
          showToast('Please drag or upload a template file (.docx/.pdf).', 'warning')
          setTemplateSaving(false)
          return
        }
        formData.append('file', templateFile)

        await apiRequest('/templates/import', {
          method: 'POST',
          token: auth.token,
          formData,
        })
        showToast('New report template imported successfully.', 'success')
      }

      setTemplateForm(emptyTemplate)
      setTemplateFile(null)
      setEditingTemplateId(null)
      await refreshCollections()
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setTemplateSaving(false)
    }
  }

  const handleDownloadReport = async () => {
    if (!selectedTemplateId) {
      showToast('Please select a template from the list.', 'warning')
      return
    }
    if (reportFiles.length === 0) {
      showToast('Please drop or upload at least one supporting document.', 'warning')
      return
    }

    setReportLoading(true)
    try {
      const formData = new FormData()
      for (const file of reportFiles) {
        formData.append('files', file)
      }

      showToast('Compiling loan valuation report...', 'info')
      const response = await fetch(`${API_BASE}/reports/generate/${selectedTemplateId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${auth.token}`
        },
        body: formData
      })

      if (!response.ok) {
        const payload = await response.json().catch(() => ({}))
        throw new Error(payload?.detail || payload?.message || 'Report generation failed.')
      }

      const blob = await response.blob()
      const objectUrl = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = 'valuation_report.docx'
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(objectUrl)

      showToast('Valuation report generated and downloaded.', 'success')
      setReportFiles([])
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setReportLoading(false)
    }
  }

  const handleMapAndReviewFields = async () => {
    if (!selectedTemplateId) {
      showToast('Please select a template from the list.', 'warning')
      return
    }
    if (reportFiles.length === 0) {
      showToast('Please drop or upload at least one supporting document.', 'warning')
      return
    }

    setMappingReviewLoading(true)
    try {
      const formData = new FormData()
      for (const file of reportFiles) {
        formData.append('uploads', file)
      }

      showToast('Extracting & mapping document fields...', 'info')
      const result = await apiRequest(`/templates/${selectedTemplateId}/map-fields`, {
        method: 'POST',
        token: auth.token,
        formData,
      })

      setMappedData(result)
      setEditingMappedFields({})
      if (result && result.sections && result.sections.length > 0) {
        setActiveReviewSectionTab(result.sections[0].name)
      }
      showToast('Extraction and mapping complete! Please review.', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setMappingReviewLoading(false)
    }
  }

  const handleGenerateReviewedReport = async () => {
    if (!selectedTemplateId || !mappedData) return

    setReportLoading(true)
    try {
      const fieldValues = {}
      
      const walkAndCompile = (fieldsList) => {
        for (const f of fieldsList) {
          const isGroup = f.field_type === 'group' || (f.nested_fields && f.nested_fields.length > 0)
          if (isGroup) {
            walkAndCompile(f.nested_fields)
            continue
          }

          const val = editingMappedFields[f.field_code] !== undefined ? editingMappedFields[f.field_code] : (f.extracted_value || '')
          const payload = {
            value: val,
            confidence: f.confidence || 1.0,
            needs_review: f.needs_review || false
          }

          if (f.field_code) {
            fieldValues[f.field_code] = payload
          }
          if (f.label) {
            fieldValues[f.label] = payload
            const slug = f.label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/(^_+|_+$)/g, '')
            if (slug) {
              fieldValues[slug] = payload
            }
          }
        }
      }

      for (const section of mappedData.sections) {
        walkAndCompile(section.fields || [])
      }

      showToast('Compiling loan valuation report...', 'info')
      const result = await apiRequest(`/templates/${selectedTemplateId}/generate-report`, {
        method: 'POST',
        token: auth.token,
        body: fieldValues
      })

      if (result && result.report_url) {
        const response = await fetch(`${API_BASE}${result.report_url}`, {
          headers: {
            Authorization: `Bearer ${auth.token}`
          }
        })

        if (!response.ok) {
          throw new Error('Report download failed.')
        }

        const blob = await response.blob()
        const objectUrl = URL.createObjectURL(blob)
        const anchor = document.createElement('a')
        anchor.href = objectUrl
        anchor.download = 'valuation_report_reviewed.docx'
        document.body.appendChild(anchor)
        anchor.click()
        anchor.remove()
        URL.revokeObjectURL(objectUrl)

        showToast('Reviewed valuation report downloaded successfully.', 'success')
        setMappedData(null)
        setEditingMappedFields({})
        setReportFiles([])
      } else {
        throw new Error('Report URL not returned by compiler endpoint.')
      }
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setReportLoading(false)
    }
  }

  const handlePermissionSubmit = async () => {
    if (!permissionFile) {
      showToast('Please upload or drag a document first.', 'warning')
      return
    }
    setPermissionLoading(true)
    try {
      const formData = new FormData()
      formData.append('upload', permissionFile)
      
      showToast('Uploading & parsing document details...', 'info')
      const result = await apiRequest('/documents/permission-number', {
        method: 'POST',
        token: auth.token,
        formData,
      })
      setPermissionResult(result)
      
      if (result && result.analysis) {
        const flat = {}
        for (const [key, field] of Object.entries(result.analysis)) {
          if (field && typeof field === 'object' && 'value' in field) {
            flat[key] = field.value !== null && field.value !== undefined ? String(field.value) : ''
          } else {
            flat[key] = field !== null && field !== undefined ? String(field) : ''
          }
        }
        setEditingAnalysis(flat)
      }
      showToast('OCR extraction completed successfully.', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    } finally {
      setPermissionLoading(false)
    }
  }

  const handleDownloadPermissionResult = async () => {
    if (!permissionResult || !editingAnalysis) return

    try {
      const tableRows = [
        new TableRow({
          children: [
            new TableCell({
              children: [new Paragraph({ children: [new TextRun({ text: "Field Name", bold: true })] })],
              width: { size: 35, type: WidthType.PERCENTAGE },
            }),
            new TableCell({
              children: [new Paragraph({ children: [new TextRun({ text: "Extracted Value", bold: true })] })],
              width: { size: 65, type: WidthType.PERCENTAGE },
            }),
          ],
        }),
      ];

      for (const item of UI_FIELDS_ORDER) {
        const val = editingAnalysis[item.key];
        const valStr = val === null || val === undefined ? "-" : String(val);
        const friendlyKey = item.label;

        tableRows.push(
          new TableRow({
            children: [
              new TableCell({
                children: [new Paragraph({ children: [new TextRun({ text: friendlyKey, bold: true, size: 20 })] })],
                width: { size: 35, type: WidthType.PERCENTAGE },
              }),
              new TableCell({
                children: [new Paragraph({ children: [new TextRun({ text: valStr, size: 20 })] })],
                width: { size: 65, type: WidthType.PERCENTAGE },
              }),
            ],
          })
        );
      }

      const docTable = new Table({
        rows: tableRows,
        width: {
          size: 100,
          type: WidthType.PERCENTAGE,
        },
        margins: {
          top: 140,
          bottom: 140,
          left: 200,
          right: 200,
        },
      });

      const doc = new Document({
        sections: [
          {
            properties: {},
            children: [
              docTable,
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
      showToast('Document downloaded.', 'success')
    } catch (err) {
      showToast(err.message, 'error')
    }
  }

  const handleDelete = async (path, id) => {
    if (!window.confirm('Are you sure you want to delete this record?')) return
    try {
      await apiRequest(`${path}/${id}`, { method: 'DELETE', token: auth.token })
      await refreshCollections()
      showToast('Record deleted successfully.', 'success')
    } catch (err) {
      showToast(err.message, 'error')
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
    showToast('Editing Valuer profile.', 'info')
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
    showToast('Editing HLC record.', 'info')
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
    showToast('Editing Template metadata.', 'info')
  }

  // Drag and drop helper handlers
  const handleDrag = (e, setDragOver) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragOver(true)
    } else if (e.type === 'dragleave') {
      setDragOver(false)
    }
  }

  if (!authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12 relative overflow-hidden animate-fade-in">
        {/* Soft background decor blobs */}
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-teal/5 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-gold/5 blur-[120px] pointer-events-none" />

        <div className="w-full max-w-5xl grid gap-8 lg:grid-cols-[1.1fr_0.9fr] relative z-10">
          {/* Welcome Info Card */}
          <section className="panel p-8 md:p-12 flex flex-col justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-teal/20 bg-teal/5 px-4 py-1.5 text-xs font-bold uppercase tracking-wider text-teal">
                <span className="w-2 h-2 rounded-full bg-teal animate-pulse" />
                Home Loan Valuation AI
              </div>
              <h1 className="mt-8 font-display text-4xl md:text-5xl lg:text-6xl font-extrabold leading-tight text-slate-900">
                Automate loan valuation reports in minutes.
              </h1>
              <p className="mt-6 text-base md:text-lg text-slate-600 leading-relaxed max-w-md">
                Register freelancers, manage valuer panels, coordinate with HLC records, and extract detailed text parameters using AI-powered OCR.
              </p>
            </div>

            <div className="mt-12 grid gap-4 sm:grid-cols-3">
              {[
                ['Secure Session', 'Bearer tokens and hashed storage', '🔐'],
                ['Universal OCR', 'PDF, images, scan and docx support', '📄'],
                ['Structured SQL', 'Relational database architecture', '🗄️'],
              ].map(([title, text, emoji]) => (
                <div key={title} className="rounded-2xl border border-slate-100 bg-white/50 p-4 transition-all hover:bg-white hover:shadow-sm">
                  <div className="text-xl mb-1">{emoji}</div>
                  <div className="text-sm font-bold text-slate-800">{title}</div>
                  <div className="mt-1 text-xs text-slate-500 leading-relaxed">{text}</div>
                </div>
              ))}
            </div>
          </section>

          {/* Form Card */}
          <section className="panel p-6 md:p-8 flex flex-col justify-center">
            <div className="flex gap-2 rounded-xl bg-slate-100 p-1 mb-8">
              <button
                className={`tab flex-1 justify-center ${mode === 'login' ? 'tab-active' : 'tab-inactive'}`}
                onClick={() => { setMode('login'); setAuthForm(emptyAuth); }}
              >
                Login
              </button>
              <button
                className={`tab flex-1 justify-center ${mode === 'register' ? 'tab-active' : 'tab-inactive'}`}
                onClick={() => { setMode('register'); setAuthForm(emptyAuth); }}
              >
                Register
              </button>
            </div>

            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              {mode === 'register' ? 'Create Freelancer Account' : 'Welcome Back'}
            </h2>
            <p className="text-sm text-slate-500 mb-6">
              {mode === 'register' ? 'Get started by creating a new account.' : 'Sign in to access your valuation dashboard.'}
            </p>

            <form className="space-y-4" onSubmit={handleAuthSubmit}>
              <div>
                <label className="label">Username</label>
                <input
                  className="field"
                  placeholder="john_doe"
                  value={authForm.username}
                  onChange={(event) => setAuthForm({ ...authForm, username: event.target.value })}
                />
              </div>
              <div>
                <label className="label">Password</label>
                <input
                  className="field"
                  type="password"
                  placeholder="••••••••"
                  value={authForm.password}
                  onChange={(event) => setAuthForm({ ...authForm, password: event.target.value })}
                />
              </div>
              {mode === 'register' && (
                <div>
                  <label className="label">Confirm Password</label>
                  <input
                    className="field"
                    type="password"
                    placeholder="••••••••"
                    value={authForm.confirmPassword}
                    onChange={(event) => setAuthForm({ ...authForm, confirmPassword: event.target.value })}
                  />
                </div>
              )}
              <button className="btn-primary w-full mt-4" type="submit">
                {mode === 'register' ? 'Create Account' : 'Sign In'}
              </button>
            </form>
          </section>
        </div>

        {/* Toasts list */}
        <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full px-4 sm:px-0">
          {toasts.map(toast => (
            <div key={toast.id} className={`p-4 rounded-2xl shadow-xl flex items-center justify-between border animate-slide-up bg-white/95 backdrop-blur-sm ${toast.type === 'success' ? 'border-emerald-200 text-emerald-800 bg-emerald-50/90' : toast.type === 'error' ? 'border-rose-200 text-rose-800 bg-rose-50/90' : toast.type === 'warning' ? 'border-amber-200 text-amber-800 bg-amber-50/90' : 'border-blue-200 text-blue-800 bg-blue-50/90'}`}>
              <div className="flex items-center gap-3">
                {toast.type === 'success' && <svg className="w-5 h-5 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                {toast.type === 'error' && <svg className="w-5 h-5 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                {toast.type === 'warning' && <svg className="w-5 h-5 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
                {toast.type === 'info' && <svg className="w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
                <span className="text-sm font-semibold">{toast.message}</span>
              </div>
              <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} className="text-slate-400 hover:text-slate-600 ml-4"><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50/50 text-slate-800">
      
      {/* Sidebar Navigation */}
      <aside className={`fixed inset-y-0 left-0 z-40 w-72 bg-white border-r border-slate-100 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0 lg:static lg:h-screen shrink-0 ${mobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div>
          {/* Logo Section */}
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-teal to-indigo-600 flex items-center justify-center text-white shadow-md shadow-teal/10">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <div>
                <h2 className="font-extrabold text-sm text-slate-800 leading-tight">Valuation AI</h2>
                <p className="text-[10px] text-teal uppercase tracking-widest font-bold font-display">Hub Management</p>
              </div>
            </div>
            {/* Close sidebar button on mobile */}
            <button onClick={() => setMobileSidebarOpen(false)} className="lg:hidden text-slate-400 hover:text-slate-600 p-1">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Links Section */}
          <nav className="p-4 space-y-1.5">
            {[
              ['templates', 'Template Management', (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              )],
              ['permission', 'Document Workspace', (
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              )],
            ].map(([key, label, icon]) => (
              <button
                key={key}
                className={`w-full rounded-2xl px-4 py-3.5 flex items-center gap-3 text-sm font-semibold transition-all duration-200 ${activeSection === key ? 'bg-slate-900 text-white shadow-lg shadow-slate-900/10' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'}`}
                onClick={() => { setActiveSection(key); setMobileSidebarOpen(false); }}
                type="button"
              >
                {icon}
                {label}
              </button>
            ))}
          </nav>
        </div>

        {/* Verification Links (Sticky Bottom) */}
        <div className="p-4 border-t border-slate-100">
          <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
              <span>Verification Channels</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
            </h4>
            <div className="space-y-2">
              <a
                className="w-full text-xs font-semibold text-slate-700 bg-white border border-slate-100 rounded-xl px-3 py-2.5 flex items-center justify-between hover:bg-slate-50 hover:border-slate-200 transition"
                href="https://dpms.ghmc.telangana.gov.in/AutoDCR.Common2/CitizenSearch/publicsearch.aspx?sName=GHMC&edFlag=0&iVal=1"
                target="_blank"
                rel="noreferrer"
              >
                <span>GHMC Public Search</span>
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
              </a>
              <a
                className="w-full text-xs font-semibold text-slate-700 bg-white border border-slate-100 rounded-xl px-3 py-2.5 flex items-center justify-between hover:bg-slate-50 hover:border-slate-200 transition"
                href="https://app.buildnow.telangana.gov.in/login"
                target="_blank"
                rel="noreferrer"
              >
                <span>Telangana BuildNow</span>
                <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
              </a>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Workspace Frame */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Workspace Header */}
        <header className="bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            {/* Hamburger button on mobile */}
            <button onClick={() => setMobileSidebarOpen(true)} className="lg:hidden p-1.5 text-slate-500 hover:text-slate-800 rounded-xl hover:bg-slate-50">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest leading-none">Workspace</p>
              <h2 className="mt-1.5 font-display text-xl md:text-2xl font-bold text-slate-900">{greeting}</h2>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <span className="hidden md:inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-600">
              <span className="w-1.5 h-1.5 rounded-full bg-teal" />
              User ID: {auth.user.user_id}
            </span>
            <button className="btn-secondary px-4 py-2" onClick={() => auth.logout()} type="button">
              <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
              Logout
            </button>
          </div>
        </header>

        {/* Workspace Body */}
        <main className="flex-1 p-6 space-y-6 max-w-6xl w-full mx-auto animate-slide-up">
          






          {/* Report Templates Section */}
          {activeSection === 'templates' && (
            <div className="grid gap-6 xl:grid-cols-[400px_1fr]">
              {/* Add Template */}
              <div className="panel p-6 h-fit">
                <h3 className="font-display text-2xl font-bold text-slate-900 mb-1">
                  {editingTemplateId ? 'Edit Template Info' : 'Store Template'}
                </h3>
                <p className="text-xs text-slate-500 mb-6">
                  Save mapping schema parameters and upload banking template files.
                </p>

                <div className="space-y-4">
                  <div>
                    <label className="label">Template Key ID</label>
                    <input
                      className="field"
                      placeholder="e.g. sbi_retail_2026"
                      value={templateForm.template_key_id}
                      onChange={(event) => setTemplateForm({ ...templateForm, template_key_id: event.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Template Name</label>
                    <input
                      className="field"
                      placeholder="e.g. SBI Retail Valuation Layout"
                      value={templateForm.template_name}
                      onChange={(event) => setTemplateForm({ ...templateForm, template_name: event.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Associated Bank</label>
                    <input
                      className="field"
                      placeholder="e.g. State Bank of India"
                      value={templateForm.template_bank}
                      onChange={(event) => setTemplateForm({ ...templateForm, template_bank: event.target.value })}
                    />
                  </div>
                  <div>
                    <label className="label">Template Content Mapping (JSON)</label>
                    <textarea
                      className="field min-h-36 font-mono text-xs leading-normal bg-slate-50/50"
                      value={templateForm.template_content_json}
                      onChange={(event) => setTemplateForm({ ...templateForm, template_content_json: event.target.value })}
                    />
                  </div>

                  {/* Drag and drop zone for templates */}
                  {!editingTemplateId && (
                    <div>
                      <label className="label">Template File (.docx or .pdf)</label>
                      <div
                        onDragEnter={(e) => handleDrag(e, setTemplateDragOver)}
                        onDragOver={(e) => handleDrag(e, setTemplateDragOver)}
                        onDragLeave={(e) => handleDrag(e, setTemplateDragOver)}
                        onDrop={(e) => {
                          e.preventDefault()
                          e.stopPropagation()
                          setTemplateDragOver(false)
                          const files = e.dataTransfer.files
                          if (files && files.length > 0) {
                            setTemplateFile(files[0])
                            showToast(`Loaded ${files[0].name}`, 'info')
                          }
                        }}
                        className={`border-2 border-dashed rounded-2xl p-6 text-center transition ${templateDragOver ? 'border-teal bg-teal/5' : 'border-slate-200 hover:border-slate-300 bg-white'}`}
                      >
                        <input
                          id="template-upload-input"
                          type="file"
                          accept=".docx,.pdf"
                          className="hidden"
                          onChange={(e) => {
                            if (e.target.files?.[0]) {
                              setTemplateFile(e.target.files[0])
                            }
                          }}
                        />
                        <label htmlFor="template-upload-input" className="cursor-pointer flex flex-col items-center">
                          <svg className="w-8 h-8 text-slate-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                          <span className="text-xs font-bold text-slate-700">Drag file here or click to select</span>
                          <span className="text-[10px] text-slate-400 mt-1">Accepts DOCX or PDF layouts</span>
                        </label>
                      </div>
                      
                      {templateFile && (
                        <div className="mt-3 flex items-center justify-between p-3 bg-slate-50 border border-slate-100 rounded-xl">
                          <div className="flex items-center gap-2 min-w-0">
                            <svg className="w-5 h-5 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                            <span className="text-xs font-medium text-slate-700 truncate">{templateFile.name}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setTemplateFile(null)}
                            className="text-rose-500 hover:bg-rose-50 p-1 rounded-lg"
                          >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  <div className="flex gap-2 pt-2">
                    <button
                      className="btn-primary flex-1"
                      onClick={handleTemplateSave}
                      disabled={templateSaving}
                      type="button"
                    >
                      {templateSaving ? 'Saving...' : editingTemplateId ? 'Update Template' : 'Save Template'}
                    </button>
                    <button
                      className="btn-secondary"
                      onClick={() => { setTemplateForm(emptyTemplate); setTemplateFile(null); setEditingTemplateId(null); }}
                      type="button"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>

              {/* Template Grid Preview & Report Compiler */}
              <div className="panel p-6 space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="font-display text-2xl font-bold text-slate-900">Registered Layouts</h3>
                </div>

                {/* Selected Template Compiler Panel */}
                {selectedTemplateId && (
                  <div className="rounded-3xl border border-teal/20 bg-teal/5 p-6 shadow-sm animate-fade-in">
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="inline-flex rounded-full bg-teal-100 text-teal-800 text-[10px] font-bold px-2.5 py-1 uppercase tracking-wider">
                          Selected Compilation Template
                        </span>
                        <h4 className="mt-2 text-lg font-extrabold text-slate-800">
                          {templates.find(t => t.template_id === selectedTemplateId)?.template_name}
                        </h4>
                      </div>
                      <button
                        type="button"
                        onClick={() => { setSelectedTemplateId(null); setReportFiles([]); }}
                        className="text-slate-400 hover:text-slate-600 bg-white/50 p-1.5 rounded-full hover:shadow-sm"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                      </button>
                    </div>

                    {!mappedData && (
                      <p className="mt-2 text-xs text-slate-500 leading-relaxed">
                        Upload the supporting documents (AOS deeds, bank Work Orders, blueprints, RERA certificates) to compile them directly into this valuation template.
                      </p>
                    )}

                    <div className="mt-4 space-y-4">
                      {!mappedData ? (
                        <>
                          {/* Report drag and drop zone */}
                          <div
                            onDragEnter={(e) => handleDrag(e, setReportDragOver)}
                            onDragOver={(e) => handleDrag(e, setReportDragOver)}
                            onDragLeave={(e) => handleDrag(e, setReportDragOver)}
                            onDrop={(e) => {
                              e.preventDefault()
                              e.stopPropagation()
                              setReportDragOver(false)
                              const files = e.dataTransfer.files
                              if (files && files.length > 0) {
                                setReportFiles(Array.from(files))
                                showToast(`Loaded ${files.length} documents for compile`, 'info')
                              }
                            }}
                            className={`border-2 border-dashed rounded-2xl p-6 text-center transition ${reportDragOver ? 'border-teal bg-teal/10' : 'border-teal/20 hover:border-teal/40 bg-white'}`}
                          >
                            <input
                              id="report-files-input"
                              type="file"
                              multiple
                              accept=".pdf,.docx,.jpg,.jpeg,.png,.webp"
                              className="hidden"
                              onChange={(e) => {
                                if (e.target.files) {
                                  setReportFiles(Array.from(e.target.files))
                                }
                              }}
                            />
                            <label htmlFor="report-files-input" className="cursor-pointer flex flex-col items-center">
                              <svg className="w-8 h-8 text-teal mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
                              <span className="text-xs font-bold text-slate-700">Drag files here or click to select</span>
                              <span className="text-[10px] text-slate-400 mt-1">Load PDF, DOCX, or scanned images</span>
                            </label>
                          </div>

                          {reportFiles.length > 0 && (
                            <div className="bg-white/80 border border-teal/10 rounded-2xl p-4">
                              <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">Supporting Files ({reportFiles.length})</h5>
                              <ul className="space-y-1.5 max-h-36 overflow-y-auto pr-2">
                                {reportFiles.map((f, i) => (
                                  <li key={i} className="text-xs text-slate-600 flex items-center justify-between p-1.5 bg-slate-50 rounded-lg">
                                    <span className="truncate pr-4">{f.name}</span>
                                    <span className="text-[10px] font-mono text-slate-400">{(f.size / 1024).toFixed(0)} KB</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          <div className="flex flex-col sm:flex-row gap-3">
                            <button
                              className="btn-accent flex-1"
                              onClick={handleDownloadReport}
                              disabled={reportLoading || mappingReviewLoading}
                              type="button"
                            >
                              {reportLoading ? (
                                <>
                                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                  Direct Generate Report
                                </>
                              ) : (
                                <>
                                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                  Direct Generate Report
                                </>
                              )}
                            </button>
                            <button
                              className="btn-secondary flex-1 border-teal/30 hover:border-teal text-teal-800 bg-white"
                              onClick={handleMapAndReviewFields}
                              disabled={reportLoading || mappingReviewLoading}
                              type="button"
                            >
                              {mappingReviewLoading ? (
                                <>
                                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-teal" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                                  Mapping Fields...
                                </>
                              ) : (
                                <>
                                  <svg className="w-4 h-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>
                                  Map & Review Fields
                                </>
                              )}
                            </button>
                          </div>
                        </>
                      ) : (
                        <div className="mt-2 border-t border-slate-200/80 pt-6 animate-fade-in space-y-6">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/5 p-4 rounded-2xl border border-slate-200/50">
                            <div>
                              <h4 className="text-sm font-extrabold text-slate-800">Review Mapped Fields</h4>
                              <p className="text-xs text-slate-500 mt-1">Verify or edit extracted template values prior to document creation.</p>
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={handleGenerateReviewedReport}
                                disabled={reportLoading}
                                className="btn-accent px-4 py-2.5 text-xs text-white"
                                type="button"
                              >
                                {reportLoading ? 'Compiling...' : 'Generate Reviewed Report (.DOCX)'}
                              </button>
                              <button
                                onClick={() => { setMappedData(null); setEditingMappedFields({}); }}
                                className="btn-secondary px-4 py-2.5 text-xs bg-white"
                                type="button"
                              >
                                Reset / Back
                              </button>
                            </div>
                          </div>

                          {/* Section Tabs Selector */}
                          <div className="border-b border-slate-200/60 bg-white/50 flex flex-wrap px-2 rounded-2xl border">
                            {mappedData.sections.map((section) => (
                              <button
                                key={section.name}
                                className={`subtab py-2.5 ${activeReviewSectionTab === section.name ? 'subtab-active' : 'subtab-inactive'}`}
                                onClick={() => setActiveReviewSectionTab(section.name)}
                                type="button"
                              >
                                {section.name}
                              </button>
                            ))}
                          </div>

                          {/* Inputs area for current section */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 bg-white p-6 rounded-3xl border border-slate-100 shadow-inner">
                            {(() => {
                              const currentSection = mappedData.sections.find(s => s.name === activeReviewSectionTab);
                              if (!currentSection) return null;

                              const renderFieldRecursive = (field, depth = 0) => {
                                const isGroup = field.field_type === 'group' || (field.nested_fields && field.nested_fields.length > 0);
                                const val = editingMappedFields[field.field_code] !== undefined ? editingMappedFields[field.field_code] : (field.extracted_value || '');
                                const isTextArea = ["property_description", "aos_property_schedule", "property_address", "purchaser_address", "approved_plan_comments", "legal_opinion", "legal_disputes", "prohibited_property_details", "mortgage_details", "ftl_buffer_zone_details", "enactment_details", "govt_enactment_details"].includes(field.field_code);

                                if (isGroup) {
                                  return (
                                    <div key={field.field_code} className="col-span-full border-l-2 border-slate-200 pl-4 py-2 my-2 bg-slate-50/20 rounded-r-xl">
                                      <h5 className="text-xs font-extrabold text-slate-800 mb-3">{field.label || field.field_code}</h5>
                                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {field.nested_fields.map(child => renderFieldRecursive(child, depth + 1))}
                                      </div>
                                    </div>
                                  );
                                }

                                const confidencePct = Math.round((field.confidence || 0) * 100);
                                let badgeColor = "bg-rose-50 text-rose-700 border-rose-100";
                                if (confidencePct >= 90) badgeColor = "bg-emerald-50 text-emerald-700 border-emerald-100";
                                else if (confidencePct >= 70) badgeColor = "bg-amber-50 text-amber-700 border-amber-100";

                                return (
                                  <div key={field.field_code} className={`flex flex-col gap-1.5 ${isTextArea ? 'col-span-full' : ''}`} style={{ paddingLeft: `${depth * 8}px` }}>
                                    <div className="flex items-center justify-between gap-2">
                                      <label className="text-xs font-bold text-slate-500 uppercase tracking-wide">
                                        {field.label || field.field_code.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}
                                      </label>
                                      <div className="flex items-center gap-1.5">
                                        <span className={`text-[10px] font-bold border rounded-full px-2 py-0.5 ${badgeColor}`}>
                                          {confidencePct}% Conf
                                        </span>
                                        {field.needs_review && (
                                          <span className="text-[10px] font-bold bg-rose-500 text-white rounded-full px-2 py-0.5 animate-pulse">
                                            Review Needed
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                    {isTextArea ? (
                                      <textarea
                                        rows={3}
                                        className="w-full bg-slate-50 hover:bg-slate-100/30 border border-slate-200 focus:border-teal focus:bg-white rounded-2xl px-4 py-3 text-sm transition focus:ring-4 focus:ring-teal/15 outline-none font-medium text-slate-700 resize-y min-h-20"
                                        value={val}
                                        onChange={(e) => setEditingMappedFields(prev => ({ ...prev, [field.field_code]: e.target.value }))}
                                      />
                                    ) : (
                                      <input
                                        type="text"
                                        className="w-full bg-slate-50 hover:bg-slate-100/30 border border-slate-200 focus:border-teal focus:bg-white rounded-2xl px-4 py-3 text-sm transition focus:ring-4 focus:ring-teal/15 outline-none font-medium text-slate-700"
                                        value={val}
                                        onChange={(e) => setEditingMappedFields(prev => ({ ...prev, [field.field_code]: e.target.value }))}
                                      />
                                    )}
                                  </div>
                                );
                              };

                              return currentSection.fields && currentSection.fields.length > 0 ? (
                                currentSection.fields.map(field => renderFieldRecursive(field))
                              ) : (
                                <div className="col-span-full py-12 text-center border border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
                                  <p className="text-sm text-slate-500 font-medium">No fields mapped in this section.</p>
                                </div>
                              );
                            })()}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Templates List */}
                {templates.length === 0 ? (
                  <div className="text-center py-12 border border-dashed border-slate-200 rounded-2xl bg-slate-50/50">
                    <p className="text-sm text-slate-500 font-medium">No templates saved yet.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {templates.map((record) => {
                      const isSelected = selectedTemplateId === record.template_id
                      return (
                        <div
                          key={record.template_id}
                          className={`rounded-2xl border p-5 transition duration-200 ${isSelected ? 'border-teal bg-teal/5 shadow-md shadow-teal/5' : 'border-slate-100 bg-white hover:border-slate-200'}`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                            <div>
                              <h4 className="font-bold text-slate-800 text-base">{record.template_name}</h4>
                              <p className="text-xs text-slate-400 mt-1 font-semibold flex items-center gap-2">
                                <span className="bg-slate-100 px-2 py-0.5 rounded-md text-slate-500">{record.template_key_id}</span>
                                <span>{record.template_bank}</span>
                              </p>
                              {record.template_preview_text && (
                                <p className="mt-3 text-xs text-slate-500 leading-relaxed max-h-16 overflow-y-auto bg-slate-50/50 p-2.5 rounded-lg border border-slate-100">
                                  {record.template_preview_text}
                                </p>
                              )}
                            </div>
                            
                            <div className="flex gap-2 shrink-0 self-end sm:self-start">
                              <button
                                className={`btn-secondary px-3 py-1.5 text-xs font-semibold ${isSelected ? 'bg-slate-900 border-slate-900 text-white hover:bg-slate-800 hover:text-white' : ''}`}
                                onClick={() => setSelectedTemplateId(record.template_id)}
                                type="button"
                              >
                                {isSelected ? 'Selected' : 'Select'}
                              </button>
                              <button
                                className="btn-secondary px-3 py-1.5 text-xs font-semibold"
                                onClick={() => openEditTemplate(record)}
                                type="button"
                              >
                                Edit
                              </button>
                              <button
                                className="btn-danger px-3 py-1.5 text-xs font-semibold"
                                onClick={() => handleDelete('/templates', record.template_id)}
                                type="button"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* OCR Permission and Extraction Section */}
          {activeSection === 'permission' && (
            <div className="space-y-6">
              
              {/* Full Width Drag and Drop Upload Card */}
              <div className="panel p-6">
                <h3 className="font-display text-2xl font-bold text-slate-900 mb-1">AOS & WO Extraction</h3>
                <p className="text-sm text-slate-500 mb-6">
                  Drop a valuation deed, sanction order, agreement of sale (AOS), or municipal layout permission to parse information.
                </p>

                <div className="grid gap-6 md:grid-cols-[1fr_200px] items-center">
                  <div
                    onDragEnter={(e) => handleDrag(e, setPermissionDragOver)}
                    onDragOver={(e) => handleDrag(e, setPermissionDragOver)}
                    onDragLeave={(e) => handleDrag(e, setPermissionDragOver)}
                    onDrop={(e) => {
                      e.preventDefault()
                      e.stopPropagation()
                      setPermissionDragOver(false)
                      const files = e.dataTransfer.files
                      if (files && files.length > 0) {
                        setPermissionFile(files[0])
                        showToast(`Loaded document: ${files[0].name}`, 'info')
                      }
                    }}
                    className={`border-2 border-dashed rounded-3xl p-8 text-center transition ${permissionDragOver ? 'border-teal bg-teal/5' : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'}`}
                  >
                    <input
                      id="permission-upload-input"
                      type="file"
                      accept=".pdf,.docx,.jpg,.jpeg,.png,.webp,.tif,.tiff"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          setPermissionFile(e.target.files[0])
                        }
                      }}
                    />
                    <label htmlFor="permission-upload-input" className="cursor-pointer flex flex-col items-center">
                      <div className="w-14 h-14 rounded-2xl bg-white flex items-center justify-center shadow-sm border border-slate-100 text-slate-400 group-hover:text-teal mb-3 transition">
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                      </div>
                      <span className="text-sm font-bold text-slate-700">Drag files here or click to browse</span>
                      <span className="text-xs text-slate-400 mt-1.5">Supports PDF, DOCX, TIFF, JPG, and PNG files up to 20MB</span>
                    </label>
                  </div>

                  <div className="space-y-3">
                    {permissionFile ? (
                      <div className="p-4 bg-teal/5 border border-teal/10 rounded-2xl animate-fade-in">
                        <div className="flex items-center gap-2 mb-2">
                          <svg className="w-4 h-4 text-teal" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                          <span className="text-xs font-bold text-teal uppercase tracking-wider">File Loaded</span>
                        </div>
                        <p className="text-xs font-bold text-slate-800 truncate" title={permissionFile.name}>
                          {permissionFile.name}
                        </p>
                        <p className="text-[10px] text-slate-400 mt-1">
                          {(permissionFile.size / 1024).toFixed(0)} KB
                        </p>
                      </div>
                    ) : (
                      <div className="p-4 bg-slate-100 rounded-2xl text-center text-xs text-slate-500 font-medium">
                        No active file chosen
                      </div>
                    )}

                    <div className="flex gap-2">
                      <button
                        className="btn-accent flex-1"
                        onClick={handlePermissionSubmit}
                        disabled={permissionLoading}
                        type="button"
                      >
                        {permissionLoading ? (
                          <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                        ) : (
                          'Extract Details'
                        )}
                      </button>
                      <button
                        className="btn-secondary px-3"
                        onClick={() => { setPermissionFile(null); setPermissionResult(null); setEditingAnalysis(null); }}
                        type="button"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Full Width Result Panel - Located in Main space */}
              {permissionResult ? (
                <div className="panel overflow-hidden animate-fade-in">
                  
                  {/* Results Heading bar */}
                  <div className="bg-slate-900 p-6 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <span className="text-[10px] font-bold text-teal uppercase tracking-widest">Extracted Results</span>
                      <h4 className="text-xl font-extrabold font-display mt-1">
                        Permission No: {editingAnalysis?.permission_number || 'Not detected'}
                      </h4>

                    </div>

                    <div className="flex gap-2.5 shrink-0 self-start md:self-center">
                      <button
                        className="btn-accent px-4 py-2.5 text-xs text-white"
                        onClick={() => {
                          navigator.clipboard.writeText(editingAnalysis?.permission_number || '')
                          showToast('Permission number copied to clipboard.', 'success')
                        }}
                        type="button"
                      >
                        Copy Permission
                      </button>
                      <button
                        className="btn-secondary px-4 py-2.5 text-xs bg-white text-slate-900 border-none hover:bg-slate-100"
                        onClick={handleDownloadPermissionResult}
                        type="button"
                      >
                        Download Results (.DOCX)
                      </button>
                    </div>
                  </div>

                  {/* Main Inputs Content Area */}
                  <div className="p-6">
                    {(() => {
                      if (!editingAnalysis) return null

                      // Helper to render a field dynamically with its label, confidence, validation checks, and text area or input
                      const renderField = (key, label, isTextArea = false) => {
                        const val = editingAnalysis[key] !== undefined ? editingAnalysis[key] : ''
                        const originalField = permissionResult?.analysis?.[key] || {}
                        const confidence = originalField.final_confidence !== undefined ? originalField.final_confidence : null
                        const status = originalField.validation_status || 'valid'
                        const msg = originalField.validation_message || ''

                        let confBadge = null
                        if (confidence !== null && confidence > 0) {
                          const percentage = Math.round(confidence * 100)
                          let badgeClass = "bg-emerald-50 text-emerald-700 border-emerald-200"
                          if (confidence < 0.5) {
                            badgeClass = "bg-rose-50 text-rose-700 border-rose-200"
                          } else if (confidence < 0.8) {
                            badgeClass = "bg-amber-50 text-amber-700 border-amber-200"
                          }
                          confBadge = (
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${badgeClass}`}>
                              {percentage}% Confidence
                            </span>
                          )
                        }

                        let borderClass = "border-slate-200 focus:border-teal focus:ring-teal/15"
                        if (status === 'invalid') {
                          borderClass = "border-rose-300 focus:border-rose-500 focus:ring-rose-500/15 bg-rose-50/10"
                        } else if (status === 'warning') {
                          borderClass = "border-amber-300 focus:border-amber-500 focus:ring-amber-500/15 bg-amber-50/10"
                        }

                        return (
                          <div key={key} className="flex flex-col gap-1.5 w-full">
                            <div className="flex justify-between items-center gap-2">
                              <label className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                                {label}
                              </label>
                              {confBadge}
                            </div>
                            
                            {isTextArea ? (
                              <textarea
                                rows={3}
                                className={`w-full bg-slate-50 hover:bg-slate-100/30 border focus:bg-white rounded-2xl px-4 py-3 text-sm transition focus:ring-4 outline-none font-medium text-slate-700 resize-y min-h-20 ${borderClass}`}
                                value={val}
                                onChange={(e) => setEditingAnalysis({ ...editingAnalysis, [key]: e.target.value })}
                              />
                            ) : (
                              <input
                                type="text"
                                className={`w-full bg-slate-50 hover:bg-slate-100/30 border focus:bg-white rounded-2xl px-4 py-3 text-sm transition focus:ring-4 outline-none font-medium text-slate-700 ${borderClass}`}
                                value={val}
                                onChange={(e) => setEditingAnalysis({ ...editingAnalysis, [key]: e.target.value })}
                              />
                            )}

                            {status !== 'valid' && msg && (
                              <div className={`flex items-start gap-1.5 mt-1 text-[11px] font-semibold leading-normal p-2.5 rounded-xl border ${
                                status === 'invalid' 
                                  ? 'bg-rose-50 text-rose-800 border-rose-100' 
                                  : 'bg-amber-50 text-amber-800 border-amber-100'
                              }`}>
                                <svg className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${status === 'invalid' ? 'text-rose-600' : 'text-amber-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                </svg>
                                <span>{msg}</span>
                              </div>
                            )}
                          </div>
                        )
                      }

                      return (
                        <div className="space-y-6">
                          {/* Grid 1: Fields 1-3 */}
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                            {renderField('inspection_date', '1. Date of inspection')}
                            {renderField('valuation_date', '2. Date of valuation')}
                            {renderField('owner_name', '3. Name of the Owner(s)')}
                          </div>

                          {/* Field 4 */}
                          <div>
                            {renderField('purchaser_details', '4. Name of the purchaser(s) and his / their address(es) with Phone no. (details of share of each owner in case of joint ownership)', true)}
                          </div>

                          {/* Field 5 */}
                          <div>
                            {renderField('property_description', '5. Brief description of the property (Including leasehold / freehold etc.)', true)}
                          </div>

                          {/* Grid 2: Fields 6-9 */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                            {renderField('prohibited_property_details', '6. Prohibited Properties Details', true)}
                            {renderField('legal_opinion', '7. Legal Opinion', true)}
                            {renderField('mortgage_details', '8. Mortgage Details', true)}
                            {renderField('ftl_buffer_zone_details', '9. FTL and Buffer Zone Details', true)}
                          </div>

                          {/* Field 10 Group */}
                          <div className="p-6 border border-slate-100 bg-slate-50/20 rounded-3xl space-y-5">
                            <div>
                              <h5 className="text-sm font-bold text-slate-800">10. Location of property</h5>
                              <p className="text-xs text-slate-400 mt-0.5">Physical location identifiers and legal boundaries of the property.</p>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                              {renderField('plot_survey_number', 'Plot No. / Survey No.')}
                              {renderField('door_house_number', 'Door No / House No')}
                              {renderField('ts_number_village', 'T.S. No. / Village')}
                              {renderField('ward_taluka', 'Ward / Taluka')}
                              {renderField('mandal_district', 'Mandal / District')}
                            </div>
                          </div>

                          {/* Field 11 */}
                          <div>
                            {renderField('property_address', '11. Postal address of the property', true)}
                          </div>
                        </div>
                      )
                    })()}
                  </div>

                  {/* Extracted Raw OCR Panel */}
                  {permissionResult.extracted_text && (
                    <div className="border-t border-slate-100 p-6 bg-slate-50/50">
                      <div className="flex justify-between items-center mb-3">
                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">Raw Extracted OCR Text</span>
                        <button
                          className="btn-secondary py-1.5 px-3 text-xs bg-white"
                          onClick={() => {
                            navigator.clipboard.writeText(permissionResult.extracted_text)
                            showToast('Raw text copied to clipboard.', 'success')
                          }}
                          type="button"
                        >
                          Copy Raw Text
                        </button>
                      </div>
                      <pre className="max-h-56 overflow-y-auto whitespace-pre-wrap text-[11px] font-mono leading-relaxed bg-slate-900 text-slate-300 p-4 rounded-2xl shadow-inner">
                        {permissionResult.extracted_text}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <div className="panel p-12 text-center border-dashed border-2 border-slate-200 bg-slate-50/50">
                  <p className="text-sm font-medium text-slate-500">
                    No active document processed. Complete the upload form above to see results.
                  </p>
                </div>
              )}
            </div>
          )}

        </main>
      </div>

      {/* Floating Toast Notifications Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-md w-full px-4 sm:px-0">
        {toasts.map(toast => (
          <div key={toast.id} className={`p-4 rounded-2xl shadow-xl flex items-center justify-between border animate-slide-up bg-white/95 backdrop-blur-sm ${toast.type === 'success' ? 'border-emerald-200 text-emerald-800 bg-emerald-50/90' : toast.type === 'error' ? 'border-rose-200 text-rose-800 bg-rose-50/90' : toast.type === 'warning' ? 'border-amber-200 text-amber-800 bg-amber-50/90' : 'border-blue-200 text-blue-800 bg-blue-50/90'}`}>
            <div className="flex items-center gap-3">
              {toast.type === 'success' && <svg className="w-5 h-5 text-emerald-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
              {toast.type === 'error' && <svg className="w-5 h-5 text-rose-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
              {toast.type === 'warning' && <svg className="w-5 h-5 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>}
              {toast.type === 'info' && <svg className="w-5 h-5 text-blue-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
              <span className="text-sm font-semibold">{toast.message}</span>
            </div>
            <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} className="text-slate-400 hover:text-slate-600 ml-4"><svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App