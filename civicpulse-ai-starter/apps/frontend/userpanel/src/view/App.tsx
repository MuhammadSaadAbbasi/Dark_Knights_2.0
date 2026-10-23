import { FormEvent, useEffect, useState } from 'react';
import { HazardSlideshow } from './HazardSlideshow';
import { BrandLogo } from './BrandLogo';
import type { HazardCategory } from '../model/hazardSlides';
import { useUserPanelViewModel } from '../viewmodel/useUserPanelViewModel';
import './style.css';

type Screen = 'home' | 'report' | 'track';

export default function App() {
  const vm = useUserPanelViewModel();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [accountLocation, setAccountLocation] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [registerMode, setRegisterMode] = useState(false);
  const [screen, setScreen] = useState<Screen>('home');
  const [photo, setPhoto] = useState<File | null>(null);
  const [location, setLocation] = useState('');
  const [description, setDescription] = useState('');
  const [hazardCategory, setHazardCategory] = useState<HazardCategory | ''>('');
  const [reference, setReference] = useState('');
  const [previewUrl, setPreviewUrl] = useState('');
  const [mapUrl, setMapUrl] = useState('');
  const [mapState, setMapState] = useState<'idle' | 'loading' | 'ready' | 'not-found'>('idle');

  useEffect(() => {
    const query = location.trim();
    if (query.length < 3) {
      setMapUrl('');
      setMapState('idle');
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setMapState('loading');
      try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query)}`, {
          signal: controller.signal,
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) throw new Error('Location lookup failed');
        const results = await response.json() as Array<{ lat: string; lon: string }>;
        const first = results[0];
        if (!first) {
          setMapUrl('');
          setMapState('not-found');
          return;
        }
        const lat = Number(first.lat);
        const lon = Number(first.lon);
        const delta = 0.008;
        const bbox = `${lon - delta},${lat - delta},${lon + delta},${lat + delta}`;
        setMapUrl(`https://www.openstreetmap.org/export/embed.html?bbox=${encodeURIComponent(bbox)}&layer=mapnik&marker=${lat}%2C${lon}`);
        setMapState('ready');
      } catch (cause) {
        if ((cause as DOMException).name !== 'AbortError') {
          setMapUrl('');
          setMapState('not-found');
        }
      }
    }, 500);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [location]);

  if (!vm.session) {
    return <main className="page auth-page">
      <div className="card auth-card">
        <BrandLogo />
        <h2>{registerMode ? 'Create your account' : 'Sign in'}</h2>
        {vm.error && <div className="alert" role="alert">{vm.error}</div>}
        <form onSubmit={(event: FormEvent) => {
          event.preventDefault();
          if (registerMode && password !== confirmPassword) return;
          void vm.signIn(username, password, registerMode, email, accountLocation);
        }}>
          <label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} minLength={3} maxLength={100} pattern="[A-Za-z0-9_.-]+" required /><small>Letters, numbers, dot, underscore, or hyphen.</small></label>
          {registerMode && <label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} maxLength={254} placeholder="you@example.com" required /><small>Used only for account contact and future updates.</small></label>}
          {registerMode && <label>Home area or neighborhood<input value={accountLocation} onChange={(event) => setAccountLocation(event.target.value)} minLength={3} maxLength={300} placeholder="Area, city, or neighborhood" required /><small>This helps us understand where community members are reporting from.</small></label>}
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} maxLength={256} required /><small>At least 8 characters.</small></label>
          {registerMode && <label>Confirm password<input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} minLength={8} required />{password !== confirmPassword && confirmPassword && <small className="field-error">Passwords do not match.</small>}</label>}
          <button disabled={vm.loading || (registerMode && password !== confirmPassword)}>{vm.loading ? 'Please wait…' : registerMode ? 'Create account' : 'Sign in'}</button>
        </form>
        <button className="text-button" onClick={() => { setRegisterMode(!registerMode); setPassword(''); setConfirmPassword(''); setEmail(''); setAccountLocation(''); }}>{registerMode ? 'Already have an account? Sign in' : 'New here? Create an account'}</button>
        <div className="demo-login"><span>Hackathon demo</span><button type="button" className="demo-button" disabled={vm.loading} onClick={() => void vm.signInAsDemo('user')}>Continue as User</button><a href="http://localhost:5174">Direct Admin Login</a></div>
        <div className="login-links"><a href="http://localhost:5174">Admin login</a></div>
      </div>
    </main>;
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      setMapState('not-found');
      return;
    }
    setMapState('loading');
    navigator.geolocation.getCurrentPosition(async ({ coords }) => {
      try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${coords.latitude}&lon=${coords.longitude}`, { headers: { Accept: 'application/json' } });
        const result = await response.json() as { display_name?: string };
        setLocation(result.display_name || `${coords.latitude.toFixed(5)}, ${coords.longitude.toFixed(5)}`);
      } catch {
        setLocation(`${coords.latitude.toFixed(5)}, ${coords.longitude.toFixed(5)}`);
      }
    }, () => setMapState('not-found'));
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    if (photo) {
      const categoryContext = hazardCategory ? `Reported hazard type: ${hazardCategory.replace(/_/g, ' ')}.` : '';
      void vm.submit(photo, location, [categoryContext, description].filter(Boolean).join(' '));
    }
  }

  function navigation() {
    return <header>
      <button className="brand-lockup brand-button" onClick={() => setScreen('home')}><BrandLogo /></button>
      <nav className="user-nav"><button className={`nav-link ${screen === 'home' ? 'active' : ''}`} onClick={() => setScreen('home')}>Home</button><button className={`nav-link ${screen === 'report' ? 'active' : ''}`} onClick={() => setScreen('report')}>Report a concern</button><button className={`nav-link ${screen === 'track' ? 'active' : ''}`} onClick={() => setScreen('track')}>Track a report</button></nav>
      <button className="text-button" onClick={vm.signOut}>Sign out</button>
    </header>;
  }

  if (screen === 'home') {
    return <main className="page">{navigation()}<section className="home-hero"><div><span className="hero-badge">✓ CIVIC INTAKE IS LIVE</span><h1>See a problem?<br /><em>Make it visible.</em></h1><p>CivicPulse helps neighbors report hazards with a photo and location, so the right people can understand what needs attention.</p><div className="hero-actions"><button onClick={() => setScreen('report')}>Report a concern →</button><button className="hero-secondary" onClick={() => setScreen('track')}>Track a report</button></div></div><div className="hero-illustration"><div className="pulse-ring" /><div className="illustration-pin">⌖</div><div className="illustration-card"><strong>Community signal</strong><small>Photo · location · action</small></div></div></section><section className="intro-section"><div><span className="eyebrow">PUBLIC SAFETY STORIES</span><h2>Real Problems. Real People. Safer Streets.</h2></div><p>One report can help prevent the next tragedy. Learn why documenting hazards clearly matters.</p></section><HazardSlideshow onReport={(category) => { setHazardCategory(category); setScreen('report'); }} /><section className="how-card"><div><span className="eyebrow">HOW CIVICPULSE WORKS</span><h2>From street-level observation to visible action.</h2><p>Your report is analyzed as a preliminary signal and sent into a review workflow. Human reviewers make the final decision.</p></div><div className="steps"><div><b>01</b><strong>Spot it</strong><small>Notice a public hazard.</small></div><div><b>02</b><strong>Submit it</strong><small>Add a photo and location.</small></div><div><b>03</b><strong>Track it</strong><small>Follow the request status.</small></div></div></section><footer><strong>CivicPulse AI</strong><span>Better information. Safer communities.</span></footer></main>;
  }

  if (screen === 'track') {
    return <main className="page">{navigation()}<section className="hero-card"><span className="hero-badge">✓ REPORT STATUS</span><h1>Track a report.</h1><p>Check the latest status of a community report using its reference ID.</p></section><section className="lookup tracking-card"><h2>Reference ID lookup</h2><p>Use the ID shown after submitting a report.</p><form onSubmit={(event) => { event.preventDefault(); void vm.lookup(reference); }}><input value={reference} onChange={(event) => setReference(event.target.value)} placeholder="Paste report reference ID" required /><button disabled={vm.loading}>Look up report →</button></form>{vm.error && <div className="alert" role="alert">{vm.error}</div>}{vm.report && <div className="tracking-result"><div className="tracking-status"><span>Current status</span><strong>{vm.report.status.replace(/_/g, ' ')}</strong></div><div className="tracking-grid"><div><small>Reference</small><strong>#{vm.report.id.slice(0, 8)}</strong></div><div><small>Category</small><strong>{vm.report.assessment?.category?.replace(/_/g, ' ') || 'Pending'}</strong></div><div><small>Severity score</small><strong>{vm.report.assessment ? `${vm.report.assessment.severity_score}/100` : 'Pending'}</strong></div><div><small>Location</small><strong>{vm.report.location_text}</strong></div></div><p className="note">AI results are preliminary. Human reviewers verify safety concerns before action.</p></div>}</section></main>;
  }

  return <main className="page">{navigation()}{vm.error && <div className="alert" role="alert">{vm.error}</div>}<section className="hero-card"><span className="hero-badge">✓ VERIFIED CIVIC INTAKE</span><h1>Make your street safer.</h1><p>Upload a clear photo and tell us where the problem is. Our AI provides a preliminary signal for human review.</p></section><section className="card report-card"><div className="card-title"><span className="step">01</span><div><span className="eyebrow">COMMUNITY REPORT</span><h2>Report a public concern</h2><p>Every report is saved securely and can be tracked with its reference ID.</p></div></div>{hazardCategory && <div className="selected-hazard"><span>Selected from safety alert</span><strong>{hazardCategory.replace(/_/g, ' ')}</strong><button type="button" className="text-button" onClick={() => setHazardCategory('')}>Clear</button></div>}<form onSubmit={submit}><label>Evidence photo <span>Required</span><input type="file" accept="image/jpeg,image/png,image/webp" required onChange={(event) => { const file = event.target.files?.[0] || null; setPhoto(file); setPreviewUrl(file ? URL.createObjectURL(file) : ''); }} /><small>JPG, PNG, or WebP · maximum 8 MB</small></label>{previewUrl && <img className="upload-preview" src={previewUrl} alt="Selected report preview" />}<label>Where is it? <span>Required</span><input required minLength={3} maxLength={300} value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Street, landmark, or nearby area" /><button type="button" className="location-button" onClick={useCurrentLocation}>⌖ Use my current location</button></label>{location.trim().length >= 3 && <div className="map-preview">{mapState === 'ready' && mapUrl ? <><iframe title="OpenStreetMap location preview" src={mapUrl} loading="lazy" /><small>Map data © OpenStreetMap contributors</small></> : <div><strong>{mapState === 'loading' ? 'Finding this location…' : mapState === 'not-found' ? 'Map preview unavailable for this text' : 'Type a location to preview it on the map'}</strong><small>You can still submit the location description.</small></div>}</div>}<label>What did you notice? <em>Optional</em><textarea rows={4} maxLength={1000} value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Describe what is visible." /></label><button disabled={vm.loading}>{vm.loading ? 'Analyzing report…' : 'Submit report →'}</button></form></section>{vm.report && <section className="card result" role="status"><span className="eyebrow">REPORT RECEIVED</span><h2>Thank you for helping.</h2><p>Reference ID</p><code>{vm.report.id}</code><div className="result-grid"><div><small>Status</small><strong>{vm.report.status}</strong></div><div><small>AI suggestion</small><strong>{vm.report.assessment?.category?.replace(/_/g, ' ') || 'Pending'}</strong></div><div><small>AI severity score</small><strong>{vm.report.assessment ? `${vm.report.assessment.severity_score}/100` : 'Pending'}</strong></div></div><button className="track-button" onClick={() => { setReference(vm.report?.id || ''); setScreen('track'); }}>Track this report →</button><p className="note">{vm.report.ai_status === 'FAILED' ? 'Automated analysis was unavailable. A human reviewer can still assess this report.' : 'AI output is preliminary. A human reviewer should verify safety concerns.'}</p></section>}</main>;
}
