/* eslint-disable react-hooks/set-state-in-effect */
import {
  AlertTriangle,
  Bot,
  Check,
  ChevronRight,
  ClipboardList,
  Home,
  Inbox,
  LogIn,
  LogOut,
  MessageSquare,
  Plus,
  RefreshCw,
  Send,
  Share2,
  UserRound,
  Wrench,
  X,
} from 'lucide-react'
import { type Dispatch, type FormEvent, type ReactNode, type SetStateAction, useCallback, useEffect, useMemo, useState } from 'react'
import { api, type AuthState } from './api'
import type {
  AiMessage,
  AiSession,
  AssetItem,
  CaseEvent,
  CaseItem,
  CaseShareRequest,
  Category,
  DiagnosticAdviceStep,
  DiagnosticChapter,
  ProfessionalProfile,
  PropertyItem,
  User,
} from './types'
import './App.css'

const AUTH_STORAGE_KEY = 'elettra-demo-auth'
const DEMO_PASSWORD = 'Password123!'

const statusLabels: Record<string, string> = {
  open: 'Aperta',
  in_diagnosis: 'In diagnosi',
  waiting_professional: 'In attesa tecnico',
  scheduled: 'Programmato',
  resolved: 'Risolto',
  closed: 'Chiuso',
  cancelled: 'Annullato',
  pending: 'In attesa',
  accepted: 'Accettata',
  rejected: 'Rifiutata',
  revoked: 'Revocata',
}

const priorityLabels: Record<string, string> = {
  low: 'Bassa',
  normal: 'Normale',
  high: 'Alta',
  urgent: 'Urgente',
}

type Notice = { tone: 'ok' | 'warn' | 'error'; text: string } | null

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function loadStoredAuth(): AuthState | null {
  const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthState
  } catch {
    return null
  }
}

function compactDate(value: string) {
  return new Intl.DateTimeFormat('it-IT', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function displayName(user: User | null) {
  if (!user) return ''
  return [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email
}

function App() {
  const [auth, setAuth] = useState<AuthState | null>(() => loadStoredAuth())
  const [user, setUser] = useState<User | null>(null)
  const [loginEmail, setLoginEmail] = useState('demo.customer@example.com')
  const [loginPassword, setLoginPassword] = useState(DEMO_PASSWORD)
  const [cases, setCases] = useState<CaseItem[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [properties, setProperties] = useState<PropertyItem[]>([])
  const [assets, setAssets] = useState<AssetItem[]>([])
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null)
  const [events, setEvents] = useState<CaseEvent[]>([])
  const [chapters, setChapters] = useState<DiagnosticChapter[]>([])
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null)
  const [adviceSteps, setAdviceSteps] = useState<DiagnosticAdviceStep[]>([])
  const [professionals, setProfessionals] = useState<ProfessionalProfile[]>([])
  const [shareRequests, setShareRequests] = useState<CaseShareRequest[]>([])
  const [aiSession, setAiSession] = useState<AiSession | null>(null)
  const [aiMessages, setAiMessages] = useState<AiMessage[]>([])
  const [aiInput, setAiInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState<Notice>(null)
  const [newCase, setNewCase] = useState({
    title: '',
    description: '',
    category_id: 0,
    property_id: 0,
    asset_id: 0,
    priority: 'normal',
  })

  const selectedCase = useMemo(
    () => cases.find((item) => item.id === selectedCaseId) ?? cases[0] ?? null,
    [cases, selectedCaseId],
  )

  const categoryById = useMemo(() => new Map(categories.map((item) => [item.id, item])), [categories])
  const propertyById = useMemo(() => new Map(properties.map((item) => [item.id, item])), [properties])
  const filteredAssets = useMemo(() => {
    if (!newCase.property_id) return assets
    return assets.filter((item) => item.property_id === newCase.property_id)
  }, [assets, newCase.property_id])

  const authenticated = Boolean(auth && user)
  const isProfessional = user?.role === 'professional'

  const showNotice = useCallback((nextNotice: Notice) => {
    setNotice(nextNotice)
    if (nextNotice) {
      window.setTimeout(() => setNotice(null), 5500)
    }
  }, [])

  const loadDashboard = useCallback(
    async (currentAuth: AuthState, currentUser: User) => {
      const [categoryData, caseData, propertyData, requestData] = await Promise.all([
        api.categories(),
        api.cases(currentAuth),
        currentUser.role === 'customer' ? api.properties(currentAuth) : Promise.resolve([]),
        currentUser.role === 'professional' ? api.shareRequests(currentAuth, 'pending') : Promise.resolve([]),
      ])
      setCategories(categoryData)
      setCases(caseData)
      setProperties(propertyData)
      setShareRequests(requestData)
      setSelectedCaseId((previous) => previous ?? caseData[0]?.id ?? null)
      if (currentUser.role === 'customer') {
        const assetData = await api.assets(currentAuth)
        setAssets(assetData)
      }
      if (categoryData.length) {
        setNewCase((previous) => (
          previous.category_id ? previous : { ...previous, category_id: categoryData[0].id }
        ))
      }
    },
    [],
  )

  const refreshAll = useCallback(async () => {
    if (!auth || !user) return
    setLoading(true)
    try {
      await loadDashboard(auth, user)
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }, [auth, loadDashboard, showNotice, user])

  useEffect(() => {
    if (!auth) return
    setLoading(true)
    api
      .me(auth)
      .then(({ user: loadedUser }) => {
        setUser(loadedUser)
        return loadDashboard(auth, loadedUser)
      })
      .catch(() => {
        window.localStorage.removeItem(AUTH_STORAGE_KEY)
        setAuth(null)
      })
      .finally(() => setLoading(false))
  }, [auth, loadDashboard])

  useEffect(() => {
    if (!selectedCase) return
    setAiSession(null)
    setAiMessages([])
    setSelectedChapterId(null)
    setAdviceSteps([])
    const loadCaseContext = async () => {
      try {
        const [chapterData, professionalData, eventData] = await Promise.all([
          api.chapters(selectedCase.category_id),
          api.professionals(selectedCase.category_id),
          auth ? api.caseEvents(auth, selectedCase.id) : Promise.resolve([]),
        ])
        setChapters(chapterData)
        setProfessionals(professionalData)
        setEvents(eventData)
        setSelectedChapterId(chapterData[0]?.id ?? null)
      } catch (error) {
        showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
      }
    }
    loadCaseContext()
  }, [auth, selectedCase, showNotice])

  useEffect(() => {
    if (!selectedChapterId) {
      setAdviceSteps([])
      return
    }
    api
      .adviceSteps(selectedChapterId)
      .then(setAdviceSteps)
      .catch((error) => showNotice({ tone: 'error', text: String(error.message) }))
  }, [selectedChapterId, showNotice])

  async function handleLogin(event: FormEvent) {
    event.preventDefault()
    const nextAuth = { email: loginEmail.trim(), password: loginPassword }
    setLoading(true)
    try {
      const response = await api.login(nextAuth)
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuth))
      setAuth(nextAuth)
      setUser(response.user)
      await loadDashboard(nextAuth, response.user)
      showNotice({ tone: 'ok', text: 'Accesso effettuato.' })
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  function logout() {
    window.localStorage.removeItem(AUTH_STORAGE_KEY)
    setAuth(null)
    setUser(null)
    setCases([])
    setSelectedCaseId(null)
  }

  async function handleCreateCase(event: FormEvent) {
    event.preventDefault()
    if (!auth) return
    setLoading(true)
    try {
      const created = await api.createCase(auth, {
        category_id: newCase.category_id,
        property_id: newCase.property_id || null,
        asset_id: newCase.asset_id || null,
        title: newCase.title,
        description: newCase.description,
        priority: newCase.priority,
      })
      setNewCase((previous) => ({ ...previous, title: '', description: '', asset_id: 0 }))
      await refreshAll()
      setSelectedCaseId(created.id)
      showNotice({ tone: 'ok', text: 'Pratica creata.' })
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  async function handleAdviceFeedback(step: DiagnosticAdviceStep, resolved: boolean) {
    if (!auth || !selectedCase) return
    setLoading(true)
    try {
      const response = await api.adviceFeedback(auth, step.id, selectedCase.id, resolved)
      await refreshAll()
      showNotice({
        tone: resolved ? 'ok' : 'warn',
        text: resolved
          ? 'Pratica marcata come risolta.'
          : `${statusLabels[response.case_status] ?? response.case_status}. Puoi continuare con AI o condivisione.`,
      })
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  async function ensureAiSession() {
    if (!auth || !selectedCase) return null
    if (aiSession) return aiSession
    const session = await api.createAiSession(auth, selectedCase.id)
    setAiSession(session)
    setAiMessages(await api.aiMessages(auth, session.id))
    return session
  }

  async function pollAiMessages(sessionId: number) {
    if (!auth) return
    for (let index = 0; index < 10; index += 1) {
      const messages = await api.aiMessages(auth, sessionId)
      setAiMessages(messages)
      const latestAssistant = [...messages].reverse().find((item) => item.role === 'assistant')
      if (latestAssistant?.status === 'completed' || latestAssistant?.status === 'failed') return
      await delay(1200)
    }
  }

  async function handleSendAi(event: FormEvent) {
    event.preventDefault()
    if (!auth || !aiInput.trim()) return
    setLoading(true)
    try {
      const session = await ensureAiSession()
      if (!session) return
      await api.sendDiagnosticTurn(auth, session.id, aiInput.trim(), selectedChapterId ?? undefined)
      setAiInput('')
      await pollAiMessages(session.id)
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  async function handleShare(professional: ProfessionalProfile) {
    if (!auth || !selectedCase || !professional.recipient_organization_id) return
    setLoading(true)
    try {
      await api.createShareRequest(auth, selectedCase.id, {
        recipient_organization_id: professional.recipient_organization_id,
        recipient_membership_id: professional.recipient_membership_id,
        share_scope: 'summary',
        visible_title: selectedCase.title,
        visible_summary: selectedCase.description || selectedCase.title,
      })
      showNotice({ tone: 'ok', text: 'Richiesta inviata al professionista.' })
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  async function handleAcceptShareRequest(shareRequest: CaseShareRequest) {
    if (!auth) return
    setLoading(true)
    try {
      const response = await api.acceptShareRequest(auth, shareRequest.id)
      await refreshAll()
      showNotice({ tone: 'ok', text: `Richiesta accettata. Conversazione #${response.conversation_id}.` })
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  async function handleRejectShareRequest(shareRequest: CaseShareRequest) {
    if (!auth) return
    setLoading(true)
    try {
      await api.rejectShareRequest(auth, shareRequest.id, 'Non disponibile per questo intervento.')
      await refreshAll()
      showNotice({ tone: 'warn', text: 'Richiesta rifiutata.' })
    } catch (error) {
      showNotice({ tone: 'error', text: String(error instanceof Error ? error.message : error) })
    } finally {
      setLoading(false)
    }
  }

  if (!authenticated) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <div className="brand-mark">
            <Home size={24} />
          </div>
          <h1>Elettra</h1>
          <form onSubmit={handleLogin} className="login-form">
            <label>
              Email
              <input value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} />
            </label>
            <label>
              Password
              <input
                type="password"
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
              />
            </label>
            <button type="submit" className="primary-button" disabled={loading}>
              <LogIn size={18} />
              Accedi
            </button>
          </form>
          <div className="demo-switch">
            <button
              type="button"
              onClick={() => {
                setLoginEmail('demo.customer@example.com')
                setLoginPassword(DEMO_PASSWORD)
              }}
            >
              <UserRound size={17} />
              Cliente demo
            </button>
            <button
              type="button"
              onClick={() => {
                setLoginEmail('demo.pro@example.com')
                setLoginPassword(DEMO_PASSWORD)
              }}
            >
              <Wrench size={17} />
              Tecnico demo
            </button>
          </div>
        </section>
        {notice && <div className={`toast ${notice.tone}`}>{notice.text}</div>}
      </main>
    )
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">
            <Home size={22} />
          </div>
          <div>
            <strong>Elettra</strong>
            <span>{isProfessional ? 'Professionista' : 'Cliente'}</span>
          </div>
        </div>
        <div className="user-box">
          <span>{displayName(user)}</span>
          <small>{user?.email}</small>
        </div>
        <button type="button" className="sidebar-action" onClick={refreshAll} disabled={loading}>
          <RefreshCw size={17} />
          Aggiorna
        </button>
        <button type="button" className="sidebar-action" onClick={logout}>
          <LogOut size={17} />
          Esci
        </button>
      </aside>

      <section className="workspace">
        <header className="workspace-header">
          <div>
            <h1>{isProfessional ? 'Richieste e pratiche' : 'Pratiche casa'}</h1>
            <p>{cases.length} pratiche, {shareRequests.length} richieste in attesa</p>
          </div>
          <span className={`connection ${loading ? 'busy' : 'ready'}`}>{loading ? 'Sincronizzo' : 'API attiva'}</span>
        </header>

        {isProfessional ? (
          <ProfessionalDashboard
            cases={cases}
            shareRequests={shareRequests}
            selectedCase={selectedCase}
            setSelectedCaseId={setSelectedCaseId}
            categoryById={categoryById}
            onAccept={handleAcceptShareRequest}
            onReject={handleRejectShareRequest}
          />
        ) : (
          <CustomerDashboard
            cases={cases}
            categories={categories}
            properties={properties}
            filteredAssets={filteredAssets}
            selectedCase={selectedCase}
            setSelectedCaseId={setSelectedCaseId}
            categoryById={categoryById}
            propertyById={propertyById}
            newCase={newCase}
            setNewCase={setNewCase}
            createCase={handleCreateCase}
            chapters={chapters}
            selectedChapterId={selectedChapterId}
            setSelectedChapterId={setSelectedChapterId}
            adviceSteps={adviceSteps}
            onAdviceFeedback={handleAdviceFeedback}
            aiMessages={aiMessages}
            aiInput={aiInput}
            setAiInput={setAiInput}
            sendAi={handleSendAi}
            professionals={professionals}
            onShare={handleShare}
            events={events}
          />
        )}
      </section>
      {notice && <div className={`toast ${notice.tone}`}>{notice.text}</div>}
    </main>
  )
}

type CustomerDashboardProps = {
  cases: CaseItem[]
  categories: Category[]
  properties: PropertyItem[]
  filteredAssets: AssetItem[]
  selectedCase: CaseItem | null
  setSelectedCaseId: (id: number) => void
  categoryById: Map<number, Category>
  propertyById: Map<number, PropertyItem>
  newCase: {
    title: string
    description: string
    category_id: number
    property_id: number
    asset_id: number
    priority: string
  }
  setNewCase: Dispatch<SetStateAction<CustomerDashboardProps['newCase']>>
  createCase: (event: FormEvent) => void
  chapters: DiagnosticChapter[]
  selectedChapterId: number | null
  setSelectedChapterId: (id: number) => void
  adviceSteps: DiagnosticAdviceStep[]
  onAdviceFeedback: (step: DiagnosticAdviceStep, resolved: boolean) => void
  aiMessages: AiMessage[]
  aiInput: string
  setAiInput: (value: string) => void
  sendAi: (event: FormEvent) => void
  professionals: ProfessionalProfile[]
  onShare: (professional: ProfessionalProfile) => void
  events: CaseEvent[]
}

function CustomerDashboard(props: CustomerDashboardProps) {
  const {
    cases,
    categories,
    properties,
    filteredAssets,
    selectedCase,
    setSelectedCaseId,
    categoryById,
    propertyById,
    newCase,
    setNewCase,
    createCase,
    chapters,
    selectedChapterId,
    setSelectedChapterId,
    adviceSteps,
    onAdviceFeedback,
    aiMessages,
    aiInput,
    setAiInput,
    sendAi,
    professionals,
    onShare,
    events,
  } = props

  return (
    <div className="grid-layout">
      <section className="panel list-panel">
        <PanelHeader icon={<ClipboardList size={19} />} title="Pratiche" />
        <div className="case-list">
          {cases.map((caseItem) => (
            <button
              type="button"
              key={caseItem.id}
              className={`case-row ${selectedCase?.id === caseItem.id ? 'active' : ''}`}
              onClick={() => setSelectedCaseId(caseItem.id)}
            >
              <span>{caseItem.title}</span>
              <small>{statusLabels[caseItem.status] ?? caseItem.status}</small>
            </button>
          ))}
        </div>
        <form className="create-case" onSubmit={createCase}>
          <h2>Nuova pratica</h2>
          <input
            placeholder="Titolo"
            value={newCase.title}
            onChange={(event) => setNewCase((previous) => ({ ...previous, title: event.target.value }))}
            required
          />
          <textarea
            placeholder="Descrizione"
            value={newCase.description}
            onChange={(event) => setNewCase((previous) => ({ ...previous, description: event.target.value }))}
          />
          <select
            value={newCase.category_id}
            onChange={(event) =>
              setNewCase((previous) => ({ ...previous, category_id: Number(event.target.value) }))
            }
          >
            {categories.map((category) => (
              <option value={category.id} key={category.id}>
                {category.name}
              </option>
            ))}
          </select>
          <select
            value={newCase.property_id}
            onChange={(event) =>
              setNewCase((previous) => ({
                ...previous,
                property_id: Number(event.target.value),
                asset_id: 0,
              }))
            }
          >
            <option value={0}>Nessun immobile</option>
            {properties.map((propertyItem) => (
              <option value={propertyItem.id} key={propertyItem.id}>
                {propertyItem.name}
              </option>
            ))}
          </select>
          <select
            value={newCase.asset_id}
            onChange={(event) => setNewCase((previous) => ({ ...previous, asset_id: Number(event.target.value) }))}
          >
            <option value={0}>Nessun asset</option>
            {filteredAssets.map((asset) => (
              <option value={asset.id} key={asset.id}>
                {asset.name}
              </option>
            ))}
          </select>
          <button type="submit" className="primary-button">
            <Plus size={17} />
            Crea
          </button>
        </form>
      </section>

      <section className="main-stack">
        {selectedCase ? (
          <>
            <section className="panel case-detail">
              <div>
                <PanelHeader icon={<Home size={19} />} title={selectedCase.title} />
                <p>{selectedCase.description || 'Nessuna descrizione.'}</p>
              </div>
              <div className="meta-grid">
                <Meta label="Stato" value={statusLabels[selectedCase.status] ?? selectedCase.status} />
                <Meta label="Priorita" value={priorityLabels[selectedCase.priority] ?? selectedCase.priority} />
                <Meta label="Categoria" value={categoryById.get(selectedCase.category_id)?.name ?? '-'} />
                <Meta label="Immobile" value={propertyById.get(selectedCase.property_id ?? 0)?.name ?? '-'} />
              </div>
            </section>

            <section className="panel">
              <PanelHeader icon={<Check size={19} />} title="Percorso guidato" />
              <div className="toolbar">
                <select
                  value={selectedChapterId ?? 0}
                  onChange={(event) => setSelectedChapterId(Number(event.target.value))}
                >
                  {chapters.map((chapter) => (
                    <option value={chapter.id} key={chapter.id}>
                      {chapter.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="advice-list">
                {adviceSteps.map((step) => (
                  <article className="advice-item" key={step.id}>
                    <div>
                      <strong>{step.title}</strong>
                      <p>{step.body}</p>
                    </div>
                    <div className="button-row">
                      <button type="button" onClick={() => onAdviceFeedback(step, true)}>
                        <Check size={16} />
                        Risolto
                      </button>
                      <button type="button" onClick={() => onAdviceFeedback(step, false)}>
                        <ChevronRight size={16} />
                        Continua
                      </button>
                    </div>
                  </article>
                ))}
                {!adviceSteps.length && <EmptyState text="Nessun consiglio salvato per questa categoria." />}
              </div>
            </section>

            <section className="panel">
              <PanelHeader icon={<Bot size={19} />} title="Diagnostica AI" />
              <div className="message-list">
                {aiMessages.map((message) => (
                  <div key={message.id} className={`message ${message.role}`}>
                    <span>{message.role === 'assistant' ? 'AI' : 'Tu'}</span>
                    <p>{message.content || statusLabels[message.status] || message.status}</p>
                    {message.error_detail && <small>{message.error_detail}</small>}
                  </div>
                ))}
                {!aiMessages.length && <EmptyState text="La chat diagnostica non ha ancora messaggi." />}
              </div>
              <form className="chat-form" onSubmit={sendAi}>
                <input
                  value={aiInput}
                  onChange={(event) => setAiInput(event.target.value)}
                  placeholder="Descrivi cosa succede"
                />
                <button type="submit" className="primary-button">
                  <Send size={17} />
                  Invia
                </button>
              </form>
            </section>
          </>
        ) : (
          <EmptyState text="Nessuna pratica disponibile." />
        )}
      </section>

      <section className="panel side-panel">
        <PanelHeader icon={<Wrench size={19} />} title="Professionisti" />
        <div className="professional-list">
          {professionals.map((professional) => (
            <article className="professional-item" key={professional.id}>
              <div>
                <strong>{professional.display_name}</strong>
                <p>{professional.service_area_text || professional.bio}</p>
              </div>
              <button
                type="button"
                onClick={() => onShare(professional)}
                disabled={!professional.recipient_organization_id || !selectedCase}
              >
                <Share2 size={16} />
                Condividi
              </button>
            </article>
          ))}
          {!professionals.length && <EmptyState text="Nessun professionista disponibile." />}
        </div>
        <PanelHeader icon={<AlertTriangle size={19} />} title="Eventi" />
        <div className="event-list">
          {events.slice(-6).map((event) => (
            <div className="event-item" key={event.id}>
              <span>{event.event_type.replaceAll('_', ' ')}</span>
              <small>{compactDate(event.created_at)}</small>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

type ProfessionalDashboardProps = {
  cases: CaseItem[]
  shareRequests: CaseShareRequest[]
  selectedCase: CaseItem | null
  setSelectedCaseId: (id: number) => void
  categoryById: Map<number, Category>
  onAccept: (shareRequest: CaseShareRequest) => void
  onReject: (shareRequest: CaseShareRequest) => void
}

function ProfessionalDashboard(props: ProfessionalDashboardProps) {
  const { cases, shareRequests, selectedCase, setSelectedCaseId, categoryById, onAccept, onReject } = props

  return (
    <div className="grid-layout professional-layout">
      <section className="panel">
        <PanelHeader icon={<Inbox size={19} />} title="Richieste ricevute" />
        <div className="request-list">
          {shareRequests.map((request) => (
            <article className="request-item" key={request.id}>
              <div>
                <strong>{request.visible_title}</strong>
                <p>{request.visible_summary || 'Riepilogo non disponibile.'}</p>
                <small>{statusLabels[request.status] ?? request.status}</small>
              </div>
              <div className="button-row">
                <button type="button" onClick={() => onAccept(request)}>
                  <Check size={16} />
                  Accetta
                </button>
                <button type="button" onClick={() => onReject(request)}>
                  <X size={16} />
                  Rifiuta
                </button>
              </div>
            </article>
          ))}
          {!shareRequests.length && <EmptyState text="Nessuna richiesta in attesa." />}
        </div>
      </section>
      <section className="panel">
        <PanelHeader icon={<ClipboardList size={19} />} title="Pratiche accessibili" />
        <div className="case-list">
          {cases.map((caseItem) => (
            <button
              type="button"
              key={caseItem.id}
              className={`case-row ${selectedCase?.id === caseItem.id ? 'active' : ''}`}
              onClick={() => setSelectedCaseId(caseItem.id)}
            >
              <span>{caseItem.title}</span>
              <small>{statusLabels[caseItem.status] ?? caseItem.status}</small>
            </button>
          ))}
        </div>
      </section>
      <section className="panel">
        <PanelHeader icon={<MessageSquare size={19} />} title={selectedCase?.title ?? 'Dettaglio'} />
        {selectedCase ? (
          <>
            <p>{selectedCase.description || 'Nessuna descrizione.'}</p>
            <div className="meta-grid">
              <Meta label="Stato" value={statusLabels[selectedCase.status] ?? selectedCase.status} />
              <Meta label="Categoria" value={categoryById.get(selectedCase.category_id)?.name ?? '-'} />
              <Meta label="Priorita" value={priorityLabels[selectedCase.priority] ?? selectedCase.priority} />
            </div>
          </>
        ) : (
          <EmptyState text="Seleziona una pratica accessibile." />
        )}
      </section>
    </div>
  )
}

function PanelHeader({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="panel-header">
      {icon}
      <h2>{title}</h2>
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="meta-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function EmptyState({ text }: { text: string }) {
  return <div className="empty-state">{text}</div>
}

export default App
