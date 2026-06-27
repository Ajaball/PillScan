/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Onboarding Screen
   3-slide intro with swipe and dot indicators
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import storage from '../js/storage.js';

const slides = [
  {
    icon: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none">
      <circle cx="60" cy="60" r="56" fill="rgba(37,99,235,0.08)" stroke="rgba(37,99,235,0.2)" stroke-width="1"/>
      <circle cx="60" cy="60" r="40" fill="rgba(37,99,235,0.12)"/>
      <rect x="42" y="38" width="36" height="44" rx="6" fill="#2563EB" opacity="0.9"/>
      <circle cx="60" cy="52" r="8" fill="white" opacity="0.9"/>
      <rect x="50" y="65" width="20" height="3" rx="1.5" fill="white" opacity="0.7"/>
      <rect x="53" y="72" width="14" height="3" rx="1.5" fill="white" opacity="0.5"/>
    </svg>`,
    titleKey: 'onboarding_title_1',
    descKey: 'onboarding_desc_1',
    color: '#2563EB',
  },
  {
    icon: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none">
      <circle cx="60" cy="60" r="56" fill="rgba(16,185,129,0.08)" stroke="rgba(16,185,129,0.2)" stroke-width="1"/>
      <circle cx="60" cy="60" r="40" fill="rgba(16,185,129,0.12)"/>
      <rect x="38" y="35" width="44" height="50" rx="6" fill="#10B981" opacity="0.9"/>
      <line x1="48" y1="48" x2="72" y2="48" stroke="white" stroke-width="2" opacity="0.7"/>
      <line x1="48" y1="56" x2="72" y2="56" stroke="white" stroke-width="2" opacity="0.5"/>
      <line x1="48" y1="64" x2="65" y2="64" stroke="white" stroke-width="2" opacity="0.5"/>
      <circle cx="50" cy="73" r="4" fill="white" opacity="0.9"/>
      <path d="M48 73l2 2 4-4" stroke="#10B981" stroke-width="1.5" stroke-linecap="round"/>
    </svg>`,
    titleKey: 'onboarding_title_2',
    descKey: 'onboarding_desc_2',
    color: '#10B981',
  },
  {
    icon: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none">
      <circle cx="60" cy="60" r="56" fill="rgba(124,58,237,0.08)" stroke="rgba(124,58,237,0.2)" stroke-width="1"/>
      <circle cx="60" cy="60" r="40" fill="rgba(124,58,237,0.12)"/>
      <path d="M40 75V50a4 4 0 014-4h32a4 4 0 014 4v25" fill="#7C3AED" opacity="0.9"/>
      <rect x="48" y="55" width="6" height="16" rx="2" fill="white" opacity="0.9"/>
      <rect x="57" y="50" width="6" height="21" rx="2" fill="white" opacity="0.7"/>
      <rect x="66" y="58" width="6" height="13" rx="2" fill="white" opacity="0.6"/>
      <circle cx="60" cy="40" r="5" fill="#FBBF24"/>
    </svg>`,
    titleKey: 'onboarding_title_3',
    descKey: 'onboarding_desc_3',
    color: '#7C3AED',
  },
];

const OnboardingPage = {
  currentSlide: 0,

  render() {
    return `
      <div class="onboarding-screen">
        <div class="onboarding-header">
          <button class="btn btn-ghost text-sm" id="skip-btn">${i18n.t('skip')}</button>
          <button class="btn btn-ghost text-sm" id="lang-toggle-btn">
            ${i18n.lang === 'ar' ? 'English' : 'العربية'}
          </button>
        </div>

        <div class="onboarding-slides" id="slides-container">
          ${slides.map((slide, i) => `
            <div class="onboarding-slide ${i === 0 ? 'active' : ''}" data-index="${i}">
              <div class="onboarding-icon animate-float">${slide.icon}</div>
              <h2 class="onboarding-title">${i18n.t(slide.titleKey)}</h2>
              <p class="onboarding-desc">${i18n.t(slide.descKey)}</p>
            </div>
          `).join('')}
        </div>

        <div class="onboarding-footer">
          <div class="onboarding-dots">
            ${slides.map((_, i) => `
              <span class="dot ${i === 0 ? 'active' : ''}" data-index="${i}"></span>
            `).join('')}
          </div>
          <button class="btn btn-primary btn-lg btn-block" id="next-btn">
            ${i18n.t('next')}
          </button>
        </div>
      </div>
    `;
  },

  mount() {
    this.currentSlide = 0;

    const nextBtn = document.getElementById('next-btn');
    const skipBtn = document.getElementById('skip-btn');
    const langBtn = document.getElementById('lang-toggle-btn');
    const container = document.getElementById('slides-container');

    nextBtn?.addEventListener('click', () => this.nextSlide());
    skipBtn?.addEventListener('click', () => this.finish());
    langBtn?.addEventListener('click', () => {
      i18n.toggleLang();
      router.navigate('/onboarding');
    });

    // Touch swipe support
    let startX = 0;
    container?.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
    }, { passive: true });

    container?.addEventListener('touchend', (e) => {
      const diff = startX - e.changedTouches[0].clientX;
      const isRTL = i18n.isRTL;
      if (Math.abs(diff) > 50) {
        if ((!isRTL && diff > 0) || (isRTL && diff < 0)) {
          this.nextSlide();
        } else {
          this.prevSlide();
        }
      }
    }, { passive: true });
  },

  nextSlide() {
    if (this.currentSlide >= slides.length - 1) {
      this.finish();
      return;
    }
    this.currentSlide++;
    this.updateSlide();
  },

  prevSlide() {
    if (this.currentSlide <= 0) return;
    this.currentSlide--;
    this.updateSlide();
  },

  updateSlide() {
    const allSlides = document.querySelectorAll('.onboarding-slide');
    const dots = document.querySelectorAll('.dot');
    const nextBtn = document.getElementById('next-btn');

    allSlides.forEach((s, i) => {
      s.classList.toggle('active', i === this.currentSlide);
    });

    dots.forEach((d, i) => {
      d.classList.toggle('active', i === this.currentSlide);
    });

    if (nextBtn) {
      nextBtn.textContent = this.currentSlide === slides.length - 1
        ? i18n.t('onboarding_start')
        : i18n.t('next');
    }
  },

  finish() {
    storage.setOnboardingDone();
    router.navigate('/login');
  },

  unmount() {}
};

export default OnboardingPage;
