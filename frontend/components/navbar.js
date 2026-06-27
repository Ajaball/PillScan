/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Bottom Navigation Bar Component
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';

const icons = {
  home: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
  scan: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/><path d="M12 3v18"/></svg>`,
  meds: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3"/></svg>`,
  history: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
  profile: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
};

function renderNavbar() {
  return `
    <nav id="bottom-navbar" class="navbar hidden">
      <div class="nav-item active" data-route="/home" id="nav-home">
        <span class="nav-icon">${icons.home}</span>
        <span class="nav-label">${i18n.t('nav_home')}</span>
      </div>
      <div class="nav-item" data-route="/scanner" id="nav-scan">
        <span class="nav-icon">${icons.scan}</span>
        <span class="nav-label">${i18n.t('nav_scan')}</span>
      </div>
      <div class="nav-item" data-route="/medications" id="nav-meds">
        <span class="nav-icon">${icons.meds}</span>
        <span class="nav-label">${i18n.t('nav_meds')}</span>
      </div>
      <div class="nav-item" data-route="/adherence" id="nav-history">
        <span class="nav-icon">${icons.history}</span>
        <span class="nav-label">${i18n.t('nav_history')}</span>
      </div>
      <div class="nav-item" data-route="/profile" id="nav-profile">
        <span class="nav-icon">${icons.profile}</span>
        <span class="nav-label">${i18n.t('nav_profile')}</span>
      </div>
    </nav>
  `;
}

function mountNavbar() {
  const navbar = document.getElementById('bottom-navbar');
  if (!navbar) return;

  navbar.addEventListener('click', (e) => {
    const item = e.target.closest('.nav-item');
    if (!item) return;

    const route = item.dataset.route;
    if (route) {
      // Haptic feedback
      if (navigator.vibrate) navigator.vibrate(10);
      router.navigate(route);
    }
  });
}

export { renderNavbar, mountNavbar };
