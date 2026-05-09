export type UserRole = 'customer' | 'professional' | 'admin'

export type User = {
  id: number
  email: string
  first_name: string
  last_name: string
  role: UserRole
  email_verified: boolean
}

export type Category = {
  id: number
  name: string
  slug: string
  description: string
}

export type CaseStatus =
  | 'open'
  | 'in_diagnosis'
  | 'waiting_professional'
  | 'scheduled'
  | 'resolved'
  | 'closed'
  | 'cancelled'

export type CaseItem = {
  id: number
  customer_user_id: number
  owner_organization_id: number
  assigned_professional_id: number | null
  category_id: number
  property_id: number | null
  asset_id: number | null
  title: string
  description: string
  status: CaseStatus
  priority: 'low' | 'normal' | 'high' | 'urgent'
  source: string
  created_at: string
  updated_at: string
}

export type PropertyItem = {
  id: number
  name: string
  city: string
}

export type AssetItem = {
  id: number
  property_id: number
  category_id: number
  name: string
  location_text: string
}

export type DiagnosticChapter = {
  id: number
  name: string
  slug: string
  description: string
  category_id: number | null
}

export type DiagnosticAdviceStep = {
  id: number
  chapter_id: number
  chapter_option_id: number | null
  title: string
  body: string
  step_type: string
  safety_level: string
  resolution_prompt: string
  next_actions_json: Array<{ code: string; label: string }>
}

export type AiSession = {
  id: number
  case_id: number | null
  status: string
  latest_assistant_message_status: string | null
}

export type AiMessage = {
  id: number
  session_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  error_detail: string
}

export type ProfessionalProfile = {
  id: number
  user_id: number
  display_name: string
  bio: string
  phone: string
  email_public: string
  service_area_text: string
  distance_km: number | null
  category_ids: number[]
  recipient_organization_id: number | null
  recipient_membership_id: number | null
}

export type CaseShareRequest = {
  id: number
  case_id: number
  status: 'pending' | 'accepted' | 'rejected' | 'revoked'
  share_scope: string
  visible_title: string
  visible_summary: string
  recipient_organization_id: number
  recipient_membership_id: number | null
  conversation_id: number | null
  created_at: string
}

export type CaseEvent = {
  id: number
  case_id: number
  event_type: string
  payload_json: Record<string, unknown>
  created_at: string
}
