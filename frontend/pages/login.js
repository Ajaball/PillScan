/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Login Page
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const LoginPage = {
  render() {
    return `
      <div class="auth-page">
        <div class="auth-bg-glow"></div>
        <div class="page-content no-navbar">
          <div class="auth-header">
            <div class="auth-logo">
              <svg width="56" height="56" viewBox="0 0 80 80" fill="none">
                <defs>
                  <linearGradient id="auth-logo-grad" x1="0" y1="0" x2="80" y2="80" gradientUnits="userSpaceOnUse">
                    <stop offset="0%" stop-color="#2563EB"/>
                    <stop offset="100%" stop-color="#7C3AED"/>
                  </linearGradient>
                </defs>
                <rect x="8" y="8" width="64" height="64" rx="18" fill="url(#auth-logo-grad)"/>
                <path d="M35 28h10v24H35z" fill="white" rx="2"/>
                <path d="M28 35h24v10H28z" fill="white" rx="2"/>
              </svg>
            </div>
            <h1 class="auth-title">${i18n.t('login_welcome')}</h1>
            <p class="auth-subtitle">${i18n.t('login_subtitle')}</p>
          </div>

          <form class="auth-form" id="login-form" novalidate>
            <div class="input-group">
              <label class="input-label">${i18n.t('email')}</label>
              <div class="input-field" id="email-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                <input type="email" id="login-email" placeholder="example@email.com" autocomplete="email" required dir="ltr">
              </div>
              <span class="input-error-text hidden" id="email-error"></span>
            </div>

            <div class="input-group">
              <label class="input-label">${i18n.t('password')}</label>
              <div class="input-field" id="password-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <input type="password" id="login-password" placeholder="••••••••" autocomplete="current-password" required>
                <button type="button" class="input-action" id="toggle-password" aria-label="Toggle password visibility">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
              <span class="input-error-text hidden" id="password-error"></span>
            </div>

            <div class="auth-actions">
              <a href="#/forgot-password" class="auth-link">${i18n.t('forgot_password')}</a>
            </div>

            <button type="submit" class="btn btn-primary btn-lg btn-block" id="login-btn">
              <span id="login-btn-text">${i18n.t('login')}</span>
              <div class="loading-dots hidden" id="login-loading">
                <span></span><span></span><span></span>
              </div>
            </button>
          </form>

          <div class="auth-footer">
            <p class="text-secondary text-sm">
              ${i18n.t('no_account')}
              <a href="#/register" class="auth-link font-semibold">${i18n.t('create_account')}</a>
            </p>
          </div>

          <div class="auth-lang-toggle">
            <button class="btn btn-ghost btn-sm" id="auth-lang-btn">
              ${i18n.lang === 'ar' ? '🌐 English' : '🌐 العربية'}
            </button>
          </div>
        </div>
      </div>
    `;
  },

  mount() {
    const form = document.getElementById('login-form');
    const emailInput = document.getElementById('login-email');
    const passwordInput = document.getElementById('login-password');
    const togglePwdBtn = document.getElementById('toggle-password');
    const langBtn = document.getElementById('auth-lang-btn');

    // Toggle password visibility
    togglePwdBtn?.addEventListener('click', () => {
      const type = passwordInput.type === 'password' ? 'text' : 'password';
      passwordInput.type = type;
    });

    // Language toggle
    langBtn?.addEventListener('click', () => {
      i18n.toggleLang();
      router.navigate('/login');
    });

    // Form submit
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleLogin(emailInput.value.trim(), passwordInput.value);
    });
  },

  async handleLogin(email, password) {
    // Validate
    let hasError = false;

    if (!email || !email.includes('@')) {
      this.showFieldError('email', i18n.t('invalid_email'));
      hasError = true;
    } else {
      this.clearFieldError('email');
    }

    if (!password || password.length < 8) {
      this.showFieldError('password', i18n.t('password_min'));
      hasError = true;
    } else {
      this.clearFieldError('password');
    }

    if (hasError) return;

    // Show loading
    this.setLoading(true);

    try {
      await api.login(email, password);
      // Get user profile
      await api.getProfile();
      toast.success(i18n.t('success'));
      router.navigate('/home');
    } catch (error) {
      toast.error(error.message || i18n.t('login_error'));
      // Shake the form
      const form = document.getElementById('login-form');
      form?.classList.add('animate-shake');
      setTimeout(() => form?.classList.remove('animate-shake'), 500);
    } finally {
      this.setLoading(false);
    }
  },

  showFieldError(field, message) {
    const errorEl = document.getElementById(`${field}-error`);
    const fieldEl = document.getElementById(`${field}-field`);
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.remove('hidden');
    }
    fieldEl?.classList.add('error');
  },

  clearFieldError(field) {
    const errorEl = document.getElementById(`${field}-error`);
    const fieldEl = document.getElementById(`${field}-field`);
    errorEl?.classList.add('hidden');
    fieldEl?.classList.remove('error');
  },

  setLoading(loading) {
    const btn = document.getElementById('login-btn');
    const text = document.getElementById('login-btn-text');
    const spinner = document.getElementById('login-loading');
    if (btn) btn.disabled = loading;
    text?.classList.toggle('hidden', loading);
    spinner?.classList.toggle('hidden', !loading);
  },

  unmount() {}
};

export default LoginPage;
