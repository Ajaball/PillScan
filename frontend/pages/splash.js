/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Splash Screen
   Premium animated splash with logo and progress bar
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import storage from '../js/storage.js';

const SplashPage = {
  render() {
    return `
      <div class="splash-screen">
        <div class="splash-bg-glow"></div>
        <div class="splash-content">
          <div class="splash-logo-wrapper splash-logo">
            <div class="splash-icon">
              <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                <defs>
                  <linearGradient id="logo-grad" x1="0" y1="0" x2="80" y2="80" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stop-color="#2563EB"/>
                    <stop offset="100%" stop-color="#7C3AED"/>
                  </linearGradient>
                </defs>
                <rect x="4" y="4" width="72" height="72" rx="20" fill="url(#logo-grad)" opacity="0.15"/>
                <rect x="12" y="12" width="56" height="56" rx="16" fill="url(#logo-grad)" opacity="0.3"/>
                <rect x="20" y="20" width="40" height="40" rx="12" fill="url(#logo-grad)"/>
                <path d="M35 32h10v16H35z" fill="white" rx="2"/>
                <path d="M32 37h16v6H32z" fill="white" rx="2"/>
              </svg>
            </div>
          </div>
          <div class="splash-text">
            <h1 class="splash-title">${i18n.t('app_name')}</h1>
            <p class="splash-subtitle">${i18n.t('app_tagline')}</p>
          </div>
          <div class="splash-progress">
            <div class="splash-progress-track">
              <div class="splash-progress-fill" id="splash-progress-bar"></div>
            </div>
          </div>
        </div>
        <div class="splash-footer splash-text">
          <p class="text-xs text-tertiary">جامعة تبوك — قسم علوم الحاسب</p>
          <p class="text-xs text-tertiary" style="margin-top:4px;">University of Tabuk — CS Department</p>
        </div>
      </div>
    `;
  },

  mount() {
    const progressBar = document.getElementById('splash-progress-bar');
    let progress = 0;

    const interval = setInterval(() => {
      progress += Math.random() * 15 + 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        // Navigate after animation
        setTimeout(() => {
          if (!storage.isOnboardingDone()) {
            router.navigate('/onboarding');
          } else if (storage.isAuthenticated()) {
            router.navigate('/home');
          } else {
            router.navigate('/login');
          }
        }, 400);
      }
      if (progressBar) {
        progressBar.style.width = `${progress}%`;
      }
    }, 200);
  },

  unmount() {}
};

export default SplashPage;
