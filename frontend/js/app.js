/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — App Initialization
   Registers routes, initializes services, and starts the app
   ═══════════════════════════════════════════════════════════════════ */

import i18n from './i18n.js';
import storage from './storage.js';
import router from './router.js';
import { renderNavbar, mountNavbar } from '../components/navbar.js';

// ── Page Imports ────────────────────────────────────────────────────
import SplashPage from '../pages/splash.js';
import OnboardingPage from '../pages/onboarding.js';
import LoginPage from '../pages/login.js';
import RegisterPage from '../pages/register.js';
import HomePage from '../pages/home.js';
import ScannerPage from '../pages/scanner.js';
import ScanResultsPage from '../pages/scan-results.js';
import LeafletScannerPage from '../pages/leaflet-scanner.js';
import LeafletSummaryPage from '../pages/leaflet-summary.js';
import DrugDetailsPage from '../pages/drug-details.js';
import DrugSearchPage from '../pages/drug-search.js';
import MedicationsPage from '../pages/medications.js';
import RemindersPage from '../pages/reminders.js';
import AdherencePage from '../pages/adherence.js';
import ProfilePage from '../pages/profile.js';
import AISettingsPage from '../pages/ai-settings.js';

class App {
  async init() {
    console.log('🚀 PillScan PWA initializing...');

    // Initialize i18n
    i18n.init();

    // Apply theme
    const theme = storage.getTheme();
    document.documentElement.setAttribute('data-theme', theme);
    this.syncThemeColor();

    // Apply font scale
    const scale = storage.getFontScale();
    document.documentElement.style.fontSize = `${16 * scale}px`;

    // Inject navbar into app
    const app = document.getElementById('app');
    if (app) {
      app.innerHTML = `
        <div id="page-container" style="position:absolute;inset:0;"></div>
        ${renderNavbar()}
      `;
    }

    // Register routes
    this.registerRoutes();

    // Mount navbar
    mountNavbar();

    // Initialize router
    router.init('page-container');

    // Listen for auth events
    window.addEventListener('auth:logout', () => {
      router.navigate('/login');
    });

    // Language change handler — re-mount navbar
    i18n.onChange(() => {
      const navEl = document.getElementById('bottom-navbar');
      if (navEl) {
        navEl.outerHTML = renderNavbar();
        mountNavbar();
      }
    });

    // Register Service Worker
    this.registerServiceWorker();

    // Handle PWA install prompt
    this.handleInstallPrompt();

    console.log('✅ PillScan PWA ready');
  }

  registerRoutes() {
    // Public routes (no auth required)
    router.register('/splash', SplashPage, { showNavbar: false });
    router.register('/onboarding', OnboardingPage, { showNavbar: false });
    router.register('/login', LoginPage, { showNavbar: false, guest: true });
    router.register('/register', RegisterPage, { showNavbar: false, guest: true });

    // Protected routes (auth required)
    router.register('/home', HomePage, { auth: true, showNavbar: true });
    router.register('/scanner', ScannerPage, { auth: true, showNavbar: false });
    router.register('/scan-results', ScanResultsPage, { auth: true, showNavbar: false });
    router.register('/leaflet-scanner', LeafletScannerPage, { auth: true, showNavbar: false });
    router.register('/leaflet-summary', LeafletSummaryPage, { auth: true, showNavbar: false });
    router.register('/drug/:id', DrugDetailsPage, { auth: true, showNavbar: false });
    router.register('/drug-search', DrugSearchPage, { auth: true, showNavbar: true });
    router.register('/medications', MedicationsPage, { auth: true, showNavbar: true });
    router.register('/reminders', RemindersPage, { auth: true, showNavbar: false });
    router.register('/adherence', AdherencePage, { auth: true, showNavbar: true });
    router.register('/profile', ProfilePage, { auth: true, showNavbar: true });
    router.register('/ai-settings', AISettingsPage, { auth: true, showNavbar: false });
  }

  /** Keep the browser chrome color in sync with the active theme */
  syncThemeColor() {
    const meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) return;

    const apply = () => {
      const isLight = document.documentElement.getAttribute('data-theme') === 'light';
      meta.setAttribute('content', isLight ? '#F8FAFC' : '#0B0F1A');
    };
    apply();

    new MutationObserver(apply).observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme'],
    });
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('📱 Service Worker registered:', registration.scope);
      } catch (error) {
        console.warn('Service Worker registration failed:', error);
      }
    }
  }

  handleInstallPrompt() {
    let deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;

      // Show install banner after a delay
      setTimeout(() => {
        if (!deferredPrompt) return;
        this.showInstallBanner(deferredPrompt);
      }, 10000); // Show after 10 seconds
    });
  }

  showInstallBanner(prompt) {
    const banner = document.createElement('div');
    banner.id = 'install-banner';
    banner.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 16px;
      right: 16px;
      max-width: 448px;
      margin: 0 auto;
      padding: 16px 20px;
      background: var(--color-surface);
      backdrop-filter: blur(20px);
      border: 1px solid var(--color-glass-border);
      border-radius: 16px;
      z-index: 100;
      display: flex;
      align-items: center;
      gap: 12px;
      animation: slideInFromBottom 0.4s ease-out;
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    `;

    banner.innerHTML = `
      <div style="flex:1;">
        <p style="font-weight:600;font-size:14px;">${i18n.t('install_prompt')}</p>
      </div>
      <button id="install-btn" style="padding:8px 16px;background:var(--color-primary-gradient);color:#fff;border:none;border-radius:10px;font-weight:600;font-size:13px;cursor:pointer;">${i18n.t('install_button')}</button>
      <button id="install-dismiss" style="padding:4px;background:none;border:none;color:var(--color-text-tertiary);cursor:pointer;font-size:13px;">${i18n.t('install_dismiss')}</button>
    `;

    document.body.appendChild(banner);

    document.getElementById('install-btn')?.addEventListener('click', async () => {
      prompt.prompt();
      const result = await prompt.userChoice;
      console.log('Install result:', result.outcome);
      banner.remove();
    });

    document.getElementById('install-dismiss')?.addEventListener('click', () => {
      banner.remove();
    });
  }
}

// ── Boot ─────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
