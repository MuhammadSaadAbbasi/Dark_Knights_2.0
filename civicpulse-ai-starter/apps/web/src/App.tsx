import { useEffect, useState } from 'react';

type Assessment = {
  category: string;
  visible_evidence: string[];
  suggested_severity: string;
  rationale: string;
  uncertainty: string;
  needs_human_review: boolean;
};
type Report = {
  id: string;
  created_at: string;
  location_text: string;
  description: string;
  status: string;
  ai_status: string;
  assessment: Assessment | null;
};
const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export default function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function loadReports() {
    setLoading(true); setError('');
    try {
      const response = await fetch(`${API}/api/admin/reports`);
      if (!response.ok) throw new Error('Could not load reports. Is the API running?');
      setReports(await response.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unexpected error');
    } finally { setLoading(false); }
  }
  useEffect(() => { void loadReports(); }, []);

  const critical = reports.filter(r => ['critical', 'high'].includes(r.assessment?.suggested_severity || '')).length;
  const needsReview = reports.filter(r => r.assessment?.needs_human_review || r.ai_status !== 'COMPLETE').length;

  return <main className="shell">
    <header className="topbar">
      <div><div className="eyebrow">CIVIC SAFETY · ADMIN</div><h1>CivicPulse <span>AI</span></h1>
      <p>Review reported hazards and verify AI suggestions.</p></div>
      <button onClick={() => void loadReports()} disabled={loading}>{loading ? 'Refreshing…' : 'Refresh reports'}</button>
    </header>
    <section className="metrics">
      <article><small>Total reports</small><strong>{reports.length}</strong></article>
      <article><small>High / critical suggestions</small><strong>{critical}</strong></article>
      <article><small>Needs review</small><strong>{needsReview}</strong></article>
    </section>
    {error && <p className="error">{error}</p>}
    <section className="panel">
      <div className="panel-head"><div><h2>Incoming reports</h2><p>AI output is preliminary and must be verified.</p></div></div>
      {reports.length === 0 && !error ? <div className="empty">No reports yet. Submit a photo through the Android app or API to see it here.</div> :
      <div className="table-wrap"><table><thead><tr><th>Report</th><th>Location</th><th>AI category</th><th>Severity</th><th>Status</th><th>Review</th></tr></thead>
      <tbody>{reports.map(r => <tr key={r.id}>
        <td><code>{r.id.slice(0, 8)}</code><small>{new Date(r.created_at).toLocaleString()}</small></td>
        <td>{r.location_text}</td><td>{r.assessment?.category || 'Pending'}</td>
        <td><span className={`pill ${(r.assessment?.suggested_severity || 'uncertain').toLowerCase()}`}>{r.assessment?.suggested_severity || 'uncertain'}</span></td>
        <td>{r.status}</td><td>{r.assessment?.needs_human_review ? 'Review required' : 'Check result'}</td>
      </tr>)}</tbody></table></div>}
    </section>
    <footer>Hackathon starter · Admin endpoints are unauthenticated in this local scaffold. Add authentication before public deployment.</footer>
  </main>;
}
