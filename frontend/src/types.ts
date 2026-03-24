export interface User {
  id: number
  email: string
  username: string
  full_name: string | null
  is_admin: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface EmailAccount {
  id: number
  email_address: string
  provider: string
  imap_host: string | null
  imap_port: number | null
  is_active: boolean
  last_scanned: string | null
  created_at: string
}

export interface ScanJob {
  id: number
  email_account_id: number
  scan_type: string
  status: string
  progress: number
  services_found: number
  error_message: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface DiscoveredService {
  id: number
  email_account_id: number
  service_name: string
  service_domain: string | null
  service_icon: string | null
  category: string | null
  detection_method: string
  status: string
  detected_at: string
  deletion_url: string | null
  deletion_difficulty: number | null
  deletion_notes: string | null
  breach_date: string | null
}

export interface DeletionRequest {
  id: number
  discovered_service_id: number
  method: string
  status: string
  generated_email_subject: string | null
  generated_email_body: string | null
  recipient_email: string | null
  notes: string | null
  requested_at: string
  confirmed_at: string | null
}

export interface DashboardStats {
  total_accounts_found: number
  active_accounts: number
  deleted_accounts: number
  pending_deletions: number
  categories: Record<string, number>
  recent_scans: ScanJob[]
}

export interface SetupCheck {
  is_setup_complete: boolean
  has_admin_user: boolean
}
