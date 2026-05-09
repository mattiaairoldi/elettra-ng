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

export type AuthState = {
  email: string
  password: string
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

function buildAuthHeader(auth: AuthState): string {
  return `Basic ${window.btoa(`${auth.email}:${auth.password}`)}`
}

async function request<T>(
  path: string,
  auth: AuthState | null,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (auth) {
    headers.set('Authorization', buildAuthHeader(auth))
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })
  if (response.status === 204) {
    return undefined as T
  }

  const contentType = response.headers.get('Content-Type') ?? ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) {
    const detail =
      typeof payload === 'string'
        ? payload
        : payload.detail ?? Object.values(payload).flat().join(' ')
    throw new Error(detail || `Request failed with status ${response.status}`)
  }
  return payload as T
}

export const api = {
  login(auth: AuthState) {
    return request<{ user: User }>('/auth/login', null, {
      method: 'POST',
      body: JSON.stringify(auth),
    })
  },
  me(auth: AuthState) {
    return request<{ user: User }>('/auth/me', auth)
  },
  categories() {
    return request<Category[]>('/categories', null)
  },
  properties(auth: AuthState) {
    return request<PropertyItem[]>('/properties', auth)
  },
  assets(auth: AuthState, propertyId?: number) {
    const query = propertyId ? `?property_id=${propertyId}` : ''
    return request<AssetItem[]>(`/assets${query}`, auth)
  },
  cases(auth: AuthState) {
    return request<CaseItem[]>('/cases', auth)
  },
  createCase(
    auth: AuthState,
    payload: {
      category_id: number
      property_id?: number | null
      asset_id?: number | null
      title: string
      description: string
      priority: string
    },
  ) {
    return request<CaseItem>('/cases', auth, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  caseEvents(auth: AuthState, caseId: number) {
    return request<CaseEvent[]>(`/cases/${caseId}/events`, auth)
  },
  chapters(categoryId?: number) {
    const query = categoryId ? `?category_id=${categoryId}` : ''
    return request<DiagnosticChapter[]>(`/diagnostic-chapters${query}`, null)
  },
  adviceSteps(chapterId: number) {
    return request<DiagnosticAdviceStep[]>(`/diagnostic-chapters/${chapterId}/advice-steps`, null)
  },
  adviceFeedback(auth: AuthState, adviceStepId: number, caseId: number, resolved: boolean) {
    return request<{ case_id: number; resolved: boolean; case_status: string; next_actions: unknown[] }>(
      `/diagnostic-advice-steps/${adviceStepId}/feedback`,
      auth,
      {
        method: 'POST',
        body: JSON.stringify({ case_id: caseId, resolved }),
      },
    )
  },
  createAiSession(auth: AuthState, caseId: number) {
    return request<AiSession>('/ai/sessions', auth, {
      method: 'POST',
      body: JSON.stringify({ case_id: caseId }),
    })
  },
  aiMessages(auth: AuthState, sessionId: number) {
    return request<AiMessage[]>(`/ai/sessions/${sessionId}/messages`, auth)
  },
  sendDiagnosticTurn(auth: AuthState, sessionId: number, content: string, chapterId?: number) {
    return request<{ user_message: AiMessage; assistant_message: AiMessage }>(
      `/ai/sessions/${sessionId}/diagnostic-turns`,
      auth,
      {
        method: 'POST',
        body: JSON.stringify({
          content,
          diagnostic_chapter_id: chapterId ?? null,
        }),
      },
    )
  },
  professionals(categoryId?: number) {
    const query = categoryId ? `?category_id=${categoryId}` : ''
    return request<ProfessionalProfile[]>(`/professionals${query}`, null)
  },
  createShareRequest(
    auth: AuthState,
    caseId: number,
    payload: {
      recipient_organization_id: number
      recipient_membership_id?: number | null
      share_scope: string
      visible_title: string
      visible_summary: string
    },
  ) {
    return request<CaseShareRequest>(`/cases/${caseId}/share-requests`, auth, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  shareRequests(auth: AuthState, status?: string) {
    const query = status ? `?status=${status}` : ''
    return request<CaseShareRequest[]>(`/case-share-requests${query}`, auth)
  },
  acceptShareRequest(auth: AuthState, id: number) {
    return request<{ share_request: CaseShareRequest; conversation_id: number }>(
      `/case-share-requests/${id}/accept`,
      auth,
      { method: 'POST' },
    )
  },
  rejectShareRequest(auth: AuthState, id: number, reason = '') {
    return request<{ share_request: CaseShareRequest }>(`/case-share-requests/${id}/reject`, auth, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  },
}
