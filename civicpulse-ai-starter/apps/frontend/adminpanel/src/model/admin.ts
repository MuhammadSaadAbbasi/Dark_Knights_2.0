export type Assessment = {
  category: string;
  suggested_severity: string;
  severity_score: number;
  rationale: string;
  uncertainty: string;
  needs_human_review: boolean;
};

export type Report = {
  id: string;
  created_at: string;
  location_text: string;
  description: string;
  status: string;
  ai_status: string;
  assessment: Assessment | null;
  verified_category?: string | null;
  verified_severity?: string | null;
  review_note?: string | null;
  reviewed_at?: string | null;
};
export type Hotspot = { location: string; report_count: number; priority_count: number; critical_count: number };

export type Session = { access_token: string; user: { username: string; role: string } };
export type AuditEvent = {
  id: number;
  actor: string;
  action: string;
  changes: { before?: Record<string, unknown>; after?: Record<string, unknown> };
  created_at: string;
};
