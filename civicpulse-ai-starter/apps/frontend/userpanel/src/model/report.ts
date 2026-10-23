export type Assessment = {
  category: string;
  visible_evidence: string[];
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

export type Session = {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: { username: string; role: string };
};
