export function BrandLogo({ compact = false }: { compact?: boolean }) {
  return <svg className={`civicpulse-logo ${compact ? 'civicpulse-logo--compact' : ''}`} viewBox={compact ? '0 0 42 42' : '0 0 210 42'} role="img" aria-label="CivicPulse AI">
    <circle cx="21" cy="21" r="18" fill="#0f766e" />
    <path d="M21 10v22M10 21h22M13.2 13.2l15.6 15.6M28.8 13.2 13.2 28.8" stroke="#fff" strokeWidth="2.3" strokeLinecap="round" />
    {!compact && <text x="49" y="27" fill="#fff" fontFamily="Georgia, serif" fontSize="20" fontWeight="700">CivicPulse</text>}
  </svg>;
}
