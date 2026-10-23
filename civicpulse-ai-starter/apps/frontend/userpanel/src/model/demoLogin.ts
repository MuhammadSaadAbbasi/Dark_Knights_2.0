import type { Session } from './report';

const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function demoLogin(role: 'user' | 'admin'): Promise<Session> {
  const response = await fetch(`${API}/api/auth/demo-login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ role }),
  });
  const payload = await response.json().catch(() => null) as { detail?: string } | null;
  if (!response.ok) throw new Error(payload?.detail || 'Demo login is unavailable.');
  return payload as Session;
}
