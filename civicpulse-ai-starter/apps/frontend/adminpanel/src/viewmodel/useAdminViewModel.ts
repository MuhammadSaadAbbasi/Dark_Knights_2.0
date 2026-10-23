import { useEffect, useState } from 'react';
import { deleteReport, demoLogin, getAudit, getHotspots, getReportImage, getReports, login, reviewReport } from '../model/adminApi';
import type { AuditEvent, Hotspot, Report, Session } from '../model/admin';

export function useAdminViewModel() {
  const [session, setSession] = useState<Session | null>(() => {
    const stored = sessionStorage.getItem('civicpulse_admin_session');
    return stored ? JSON.parse(stored) as Session : null;
  });
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [imageUrl, setImageUrl] = useState('');
  const [imageLoading, setImageLoading] = useState(false);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);

  async function signIn(username: string, password: string) {
    setLoading(true); setError('');
    try { const next = await login(username, password); setSession(next); sessionStorage.setItem('civicpulse_admin_session', JSON.stringify(next)); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to sign in.'); }
    finally { setLoading(false); }
  }

  async function signInAsDemo(role: 'user' | 'admin') {
    setLoading(true); setError('');
    try {
      const next = await demoLogin(role);
      setSession(next);
      sessionStorage.setItem('civicpulse_admin_session', JSON.stringify(next));
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Demo login is unavailable.'); }
    finally { setLoading(false); }
  }

  async function refresh(nextPage = page) {
    if (!session) return;
    setLoading(true); setError('');
    try {
      const [result, nextHotspots] = await Promise.all([
        getReports(session.access_token, nextPage),
        getHotspots(session.access_token),
      ]);
      setReports(result.reports); setTotal(result.total); setPage(nextPage); setHotspots(nextHotspots);
    }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to load reports.'); if (cause instanceof Error && cause.message.includes('session expired')) signOut(); }
    finally { setLoading(false); }
  }

  async function selectReport(id: string) {
    if (!session) return;
    setError('');
    setImageLoading(true);
    try {
      const nextAudit = await getAudit(session.access_token, id);
      setAudit(nextAudit);
      const image = await getReportImage(session.access_token, id);
      setImageUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return URL.createObjectURL(image);
      });
    }
    catch (cause) {
      setImageUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return '';
      });
      setError(cause instanceof Error ? cause.message : 'Unable to load report evidence.');
    }
    finally { setImageLoading(false); }
  }

  async function review(id: string, status: string, category: string, severity: string, note: string) {
    if (!session) return;
    setLoading(true); setError('');
    try { const updated = await reviewReport(session.access_token, id, status, category, severity, note); setReports((items) => items.map((item) => item.id === id ? updated : item)); await selectReport(id); }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save review.'); if (cause instanceof Error && cause.message.includes('session expired')) signOut(); }
    finally { setLoading(false); }
  }

  async function remove(id: string) {
    if (!session) return;
    setLoading(true); setError('');
    try {
      await deleteReport(session.access_token, id);
      setReports((items) => items.filter((item) => item.id !== id));
      setTotal((value) => Math.max(0, value - 1));
      setHotspots(await getHotspots(session.access_token));
      setAudit([]);
      setImageUrl((current) => {
        if (current) URL.revokeObjectURL(current);
        return '';
      });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to delete report.');
    } finally { setLoading(false); }
  }

  useEffect(() => { void refresh(1); }, [session]);
  function signOut() {
    setSession(null); setReports([]); setAudit([]); setPage(1); setTotal(0);
    setImageUrl((current) => { if (current) URL.revokeObjectURL(current); return ''; });
    sessionStorage.removeItem('civicpulse_admin_session');
  }
  return { session, reports, audit, hotspots, imageUrl, imageLoading, error, loading, page, total, signIn, signInAsDemo, signOut, refresh, selectReport, review, remove };
}
