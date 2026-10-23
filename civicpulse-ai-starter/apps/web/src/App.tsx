import { FormEvent, useEffect, useState } from 'react';

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

function ShieldIcon() {
  return <svg aria-hidden="true" viewBox="0 0 48 48" className="brand-icon">
    <path d="M24 4 39 10v11c0 10-6.4 18.1-15 22-8.6-3.9-15-12-15-22V10l15-6Z" />
    <path d="m16 24 5 5 11-12" className="icon-line" />
  </svg>;
}

function formatCategory(value: string) {
  return value.split('_').join(' ');
}

export default function App() {
  const [reports, setReports] = useState<Report[]>([]);
  const [activeView, setActiveView] = useState<'reports' | 'submit'>('reports');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [photo, setPhoto] = useState<File | null>(null);
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');

  async function loadReports() {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API}/api/admin/reports`);
      if (!response.ok) throw new Error('Reports could not be loaded. Check that the API is running.');
      setReports(await response.json());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadReports(); }, []);

  async function submitReport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!photo) {
      setError('Choose a JPG, PNG, or WebP photo before submitting.');
      return;
    }
    setSubmitting(true);
    setError('');
    setSuccess('');
    const formData = new FormData();
    formData.append('photo', photo);
    formData.append('location_text', location);
    formData.append('description', description);
    try {
      const response = await fetch(`${API}/api/reports`, { method: 'POST', body: formData });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || 'The report could not be submitted.');
      }
      const report: Report = await response.json();
      setSuccess(`Report ${report.id.slice(0, 8)} was submitted. It is ready for review.`);
      setPhoto(null);
      setLocation('');
      setDescription('');
      setActiveView('reports');
      await loadReports();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Something went wrong.');
    } finally {
      setSubmitting(false);
    }
  }

  const highRisk = reports.filter((report) => ['critical', 'high'].includes(
    report.assessment?.suggested_severity || '',
  )).length;
  const needsReview = reports.filter((report) =>
    report.assessment?.needs_human_review || report.ai_status !== 'COMPLETE').length;

  return <main className="shell">
    <header className="topbar">
      <div className="brand-lockup">
        <div className="brand-mark"><ShieldIcon /></div>
        <div>
          <div className="eyebrow">CIVIC SAFETY · ADMIN CONSOLE</div>
          <h1>CivicPulse <span>AI</span></h1>
          <p>Turn community observations into clear, reviewable action.</p>
        </div>
      </div>
      <button className="secondary-button" onClick={() => void loadReports()} disabled={loading}>
        <span aria-hidden="true">↻</span> {loading ? 'Refreshing' : 'Refresh'}
      </button>
    </header>

    <nav className="tabs" aria-label="Application views">
      <button className={activeView === 'reports' ? 'tab active' : 'tab'} onClick={() => setActiveView('reports')}>
        Report queue
      </button>
      <button className={activeView === 'submit' ? 'tab active' : 'tab'} onClick={() => setActiveView('submit')}>
        Submit a report
      </button>
    </nav>

    {error && <div className="notice error" role="alert"><strong>Could not complete that action.</strong> {error}</div>}
    {success && <div className="notice success" role="status">{success}</div>}

    {activeView === 'submit' ? <section className="form-card">
      <div className="section-intro">
        <div className="illustration" aria-hidden="true">
          <svg viewBox="0 0 80 80"><rect x="14" y="18" width="52" height="44" rx="8" /><circle cx="40" cy="40" r="10" /><path d="m24 18 5-7h22l5 7M55 28h.01" /></svg>
        </div>
        <div><div className="eyebrow">COMMUNITY REPORT</div><h2>Share a safety concern</h2>
          <p>Provide what you observed. The AI suggestion is preliminary and will be checked by a human.</p></div>
      </div>
      <form onSubmit={submitReport} className="report-form">
        <label>Photo <span className="required">Required</span>
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setPhoto(event.target.files?.[0] || null)} required />
          <small>{photo ? photo.name : 'JPG, PNG, or WebP · maximum 8 MB'}</small>
        </label>
        <label>Where did you see it? <span className="required">Required</span>
          <input value={location} onChange={(event) => setLocation(event.target.value)} minLength={3} maxLength={300} placeholder="Street, landmark, or nearby area" required />
        </label>
        <label>What else should reviewers know? <span className="optional">Optional</span>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={1000} rows={4} placeholder="Add visible details, access concerns, or timing." />
        </label>
        <button className="primary-button" disabled={submitting}>{submitting ? 'Submitting report…' : 'Submit report'}</button>
      </form>
    </section> : <>
      <section className="metrics">
        <article><span className="metric-icon teal" aria-hidden="true">◎</span><div><small>Total reports</small><strong>{reports.length}</strong></div></article>
        <article><span className="metric-icon amber" aria-hidden="true">!</span><div><small>High / critical</small><strong>{highRisk}</strong></div></article>
        <article><span className="metric-icon blue" aria-hidden="true">✓</span><div><small>Needs review</small><strong>{needsReview}</strong></div></article>
      </section>
      <section className="panel">
        <div className="panel-head"><div><div className="eyebrow">LIVE QUEUE</div><h2>Incoming reports</h2><p>Review AI suggestions before any action is taken.</p></div>
          <button className="primary-button compact" onClick={() => setActiveView('submit')}>＋ New report</button></div>
        {reports.length === 0 && !loading ? <div className="empty"><div className="empty-icon" aria-hidden="true">⌁</div><strong>No reports yet</strong><p>Submit a photo to start the review queue.</p></div> :
        <div className="table-wrap"><table><caption className="sr-only">Civic safety reports</caption><thead><tr><th>Report</th><th>Location</th><th>AI category</th><th>Severity</th><th>Status</th><th>Review</th></tr></thead>
          <tbody>{reports.map((report) => <tr key={report.id}>
            <td><code>#{report.id.slice(0, 8)}</code><small>{new Date(report.created_at).toLocaleString()}</small></td>
            <td>{report.location_text}</td><td className="category">{report.assessment ? formatCategory(report.assessment.category) : 'Pending'}</td>
            <td><span className={`pill ${(report.assessment?.suggested_severity || 'uncertain').toLowerCase()}`}>{report.assessment?.suggested_severity || 'uncertain'}</span></td>
            <td><span className="status-dot">{report.status}</span></td>
            <td>{report.assessment?.needs_human_review ? <span className="review-needed">Review required</span> : 'Check result'}</td>
          </tr>)}</tbody>
        </table></div>}
      </section>
    </>}
    <footer><span>AI output is a suggestion, not a verified safety determination.</span><span>Admin endpoints are local-demo only until authentication is added.</span></footer>
  </main>;
}
