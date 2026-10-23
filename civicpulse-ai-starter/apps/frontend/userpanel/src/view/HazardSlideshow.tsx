import { useEffect, useRef, useState } from 'react';
import { hazardSlides, type HazardCategory } from '../model/hazardSlides';

type HazardSlideshowProps = {
  onReport: (category: HazardCategory) => void;
};

export function HazardSlideshow({ onReport }: HazardSlideshowProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const touchStart = useRef<number | null>(null);
  const activeSlide = hazardSlides[activeIndex];

  useEffect(() => {
    setImageFailed(false);
  }, [activeIndex]);

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(media.matches);
    update();
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (paused || reducedMotion) return;
    const timer = window.setInterval(() => {
      setActiveIndex((index) => (index + 1) % hazardSlides.length);
    }, 7000);
    return () => window.clearInterval(timer);
  }, [paused]);

  function moveBy(offset: number) {
    setActiveIndex((index) => (index + offset + hazardSlides.length) % hazardSlides.length);
  }

  return <section
    className={`hazard-slideshow ${imageFailed ? 'hazard-slideshow--fallback' : ''}`}
    aria-label="Public safety alerts"
    onMouseEnter={() => setPaused(true)}
    onMouseLeave={() => setPaused(false)}
    onFocus={() => setPaused(true)}
    onBlur={() => setPaused(false)}
    onTouchStart={(event) => { touchStart.current = event.touches[0]?.clientX ?? null; }}
    onTouchEnd={(event) => {
      if (touchStart.current === null) return;
      const distance = (event.changedTouches[0]?.clientX ?? touchStart.current) - touchStart.current;
      if (Math.abs(distance) > 45) moveBy(distance < 0 ? 1 : -1);
      touchStart.current = null;
    }}
  >
    <img
      key={activeSlide.category}
      className="hazard-slide-image"
      src={activeSlide.image}
      alt={activeSlide.alt}
      onError={() => setImageFailed(true)}
    />
    <div className="hazard-slide-overlay" />
    <div className="hazard-slide-content">
      <span className="hazard-slide-eyebrow">PUBLIC SAFETY ALERT</span>
      <h2>{activeSlide.title}</h2>
      <p className="hazard-slide-supporting">{activeSlide.supportingText}</p>
      <div className={`hazard-fact ${activeIndex === 0 ? 'hazard-fact--numbered' : ''}`}>
        {activeIndex === 0 && <strong>27</strong>}
        <span>{activeSlide.fact}</span>
      </div>
      <div className="hazard-source">
        {activeSlide.sourceLabel && <span>{activeSlide.sourceLabel}</span>}
        {activeSlide.sourceUrl && <a href={activeSlide.sourceUrl} target="_blank" rel="noreferrer">Read source ↗</a>}
      </div>
      <button className="hazard-cta" onClick={() => onReport(activeSlide.category)}>{activeSlide.cta}</button>
    </div>
    <div className="hazard-slide-controls">
      <button className="hazard-arrow" aria-label="Previous hazard" onClick={() => moveBy(-1)}>←</button>
      <div className="hazard-dots" role="tablist" aria-label="Choose safety alert">
        {hazardSlides.map((slide, index) => <button
          key={slide.category}
          className={`hazard-dot ${index === activeIndex ? 'active' : ''}`}
          role="tab"
          aria-selected={index === activeIndex}
          aria-label={`Show alert ${index + 1}`}
          onClick={() => setActiveIndex(index)}
        />)}
      </div>
      <span className="hazard-counter">{String(activeIndex + 1).padStart(2, '0')} / {String(hazardSlides.length).padStart(2, '0')}</span>
      <button className="hazard-arrow" aria-label="Next hazard" onClick={() => moveBy(1)}>→</button>
    </div>
  </section>;
}
