import type { Report, Session } from './report';

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function apiError(response: Response, fallback: string): Promise<Error> {
  const payload = await response.json().catch(() => null) as { detail?: string | Array<{ msg?: string }> } | null;
  if (typeof payload?.detail === 'string') return new Error(payload.detail);
  if (Array.isArray(payload?.detail)) {
    const message = payload.detail.map((item) => item.msg).filter(Boolean).join(' ');
    if (message) return new Error(message);
  }
  if (response.status === 0) return new Error('The API is unavailable. Start the backend and try again.');
  return new Error(fallback);
}

async function request<T>(input: RequestInfo | URL, init: RequestInit, fallback: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(input, init);
  } catch {
    throw new Error('Cannot connect to the API. Make sure the backend is running at http://127.0.0.1:8000.');
  }
  if (!response.ok) throw await apiError(response, fallback);
  return response.json() as Promise<T>;
}

export async function register(username: string, password: string, email: string, location: string): Promise<Session> {
  return request<Session>(`${API}/api/auth/register`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ username: username.trim(), password, email: email.trim().toLowerCase(), location: location.trim() }) }, 'Registration failed.');
}

export async function login(username: string, password: string): Promise<Session> {
  return request<Session>(`${API}/api/auth/login`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ username: username.trim(), password }) }, 'Invalid username or password.');
}

export async function createReport(token: string, photo: File, location: string, description: string): Promise<Report> {
  const body = new FormData();
  body.append('photo', photo);
  body.append('location_text', location);
  body.append('description', description);
  return request<Report>(`${API}/api/reports`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body }, 'The report could not be submitted.');
}

export async function getReport(token: string, id: string): Promise<Report> {
  return request<Report>(`${API}/api/reports/${encodeURIComponent(id)}`, { headers: { Authorization: `Bearer ${token}` } }, 'Report not found. Check the reference ID.');
}
