import { useState } from 'react';
import { createReport, getReport, login, register } from '../model/reportApi';
import { demoLogin } from '../model/demoLogin';
import type { Report, Session } from '../model/report';

export function useUserPanelViewModel() {
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [session, setSession] = useState<Session | null>(() => {
    const stored = sessionStorage.getItem('civicpulse_user_session');
    return stored ? JSON.parse(stored) as Session : null;
  });

  async function signIn(username: string, password: string, createAccount: boolean, email = '', location = '') {
    setLoading(true); setError('');
    try {
      const next = createAccount ? await register(username, password, email, location) : await login(username, password);
      setSession(next);
      sessionStorage.setItem('civicpulse_user_session', JSON.stringify(next));
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Authentication failed.'); }
    finally { setLoading(false); }
  }

  async function signInAsDemo(role: 'user' | 'admin') {
    setLoading(true); setError('');
    try {
      const next = await demoLogin(role);
      setSession(next);
      sessionStorage.setItem('civicpulse_user_session', JSON.stringify(next));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Demo login is unavailable.');
    } finally { setLoading(false); }
  }

  async function submit(photo: File, location: string, description: string) {
    setLoading(true); setError('');
    if (!session) return;
    try { setReport(await createReport(session.access_token, photo, location, description)); }
    catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Something went wrong.';
      setError(message);
      if (message.includes('invalid or expired') || message.includes('authentication')) signOut();
    }
    finally { setLoading(false); }
  }

  async function lookup(id: string) {
    setLoading(true); setError('');
    if (!session) return;
    try { setReport(await getReport(session.access_token, id.trim())); }
    catch (cause) {
      const message = cause instanceof Error ? cause.message : 'Something went wrong.';
      setError(message);
      if (message.includes('invalid or expired') || message.includes('authentication')) signOut();
    }
    finally { setLoading(false); }
  }

  function signOut() { setSession(null); setReport(null); sessionStorage.removeItem('civicpulse_user_session'); }
  return { report, session, loading, error, signIn, signInAsDemo, signOut, submit, lookup };
}
