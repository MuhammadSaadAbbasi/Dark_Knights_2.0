import type { AuditEvent, Hotspot, Report, Session } from './admin';

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function login(username: string, password: string): Promise<Session> {
  const response = await fetch(`${API}/api/auth/login`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ username, password }) });
  if (!response.ok) throw new Error('Invalid username or password.');
  return response.json() as Promise<Session>;
}

export async function demoLogin(role: 'user' | 'admin'): Promise<Session> {
  const response = await fetch(`${API}/api/auth/demo-login`, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ role }),
  });
  const payload = await response.json().catch(() => null) as { detail?: string } | null;
  if (!response.ok) throw new Error(payload?.detail || 'Demo login is unavailable.');
  return payload as Session;
}

async function request(path: string, token: string, options: RequestInit = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { ...options.headers, Authorization: `Bearer ${token}` } });
  if (response.status === 401) throw new Error('Your session expired. Please sign in again.');
  if (!response.ok) throw new Error('The admin request could not be completed.');
  return response;
}

export async function getReports(token: string, page: number): Promise<{ reports: Report[]; total: number }> {
  const response = await request(`/api/admin/reports?page=${page}&page_size=20`, token);
  return { reports: await response.json() as Report[], total: Number(response.headers.get('X-Total-Count') || 0) };
}

export async function reviewReport(token: string, id: string, status: string, category: string, severity: string, note: string): Promise<Report> {
  const response = await request(`/api/admin/reports/${encodeURIComponent(id)}`, token, {
    method: 'PATCH', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ status, verified_category: category || null, verified_severity: severity || null, review_note: note || null }),
  });
  return response.json() as Promise<Report>;
}

export async function getAudit(token: string, id: string): Promise<AuditEvent[]> {
  return (await request(`/api/admin/reports/${encodeURIComponent(id)}/audit`, token)).json() as Promise<AuditEvent[]>;
}

export async function getReportImage(token: string, id: string): Promise<Blob> {
  const response = await request(`/api/admin/reports/${encodeURIComponent(id)}/image`, token);
  return response.blob();
}

export async function deleteReport(token: string, id: string): Promise<void> {
  await request(`/api/admin/reports/${encodeURIComponent(id)}`, token, { method: 'DELETE' });
}

export async function getHotspots(token: string): Promise<Hotspot[]> {
  return (await request('/api/admin/hotspots?limit=10', token)).json() as Promise<Hotspot[]>;
}
