/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Register Page
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const RegisterPage = {
  render() {
    return `
      <div class="auth-page">
        <div class="auth-bg-glow"></div>
        <div class="page-content no-navbar">
          <div class="auth-header compact">
            <button class="btn btn-ghost btn-icon" id="back-btn" style="position:absolute;top:16px;${i18n.isRTL ? 'right' : 'left'}:12px;">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
            </button>
            <h1 class="auth-title">${i18n.t('register_welcome')}</h1>
            <p class="auth-subtitle">${i18n.t('register_subtitle')}</p>
          </div>

          <form class="auth-form" id="register-form" novalidate>
            <div class="input-group">
              <label class="input-label">${i18n.t('full_name')} *</label>
              <div class="input-field" id="name-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                <input type="text" id="reg-name" placeholder="${i18n.t('full_name')}" autocomplete="name" required>
              </div>
              <span class="input-error-text hidden" id="name-error"></span>
            </div>

            <div class="input-group">
              <label class="input-label">${i18n.t('email')} *</label>
              <div class="input-field" id="reg-email-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                <input type="email" id="reg-email" placeholder="example@email.com" autocomplete="email" required dir="ltr">
              </div>
              <span class="input-error-text hidden" id="reg-email-error"></span>
            </div>

            <div class="input-group">
              <label class="input-label">${i18n.t('phone')} *</label>
              <div class="input-field" id="reg-phone-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                <input type="tel" id="reg-phone" placeholder="+966 5XX XXX XXXX" autocomplete="tel" dir="ltr" required>
              </div>
              <span class="input-error-text hidden" id="reg-phone-error"></span>
            </div>

            <div class="input-group">
              <label class="input-label">${i18n.t('password')} *</label>
              <div class="input-field" id="reg-password-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <input type="password" id="reg-password" placeholder="••••••••" autocomplete="new-password" required>
                <button type="button" class="input-action" id="toggle-reg-pwd">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
              </div>
              <span class="input-error-text hidden" id="reg-password-error"></span>
            </div>

            <div class="input-group">
              <label class="input-label">${i18n.t('confirm_password')} *</label>
              <div class="input-field" id="confirm-password-field">
                <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <input type="password" id="reg-confirm-password" placeholder="••••••••" autocomplete="new-password" required>
              </div>
              <span class="input-error-text hidden" id="confirm-password-error"></span>
            </div>

            <button type="submit" class="btn btn-primary btn-lg btn-block mt-4" id="register-btn">
              <span id="register-btn-text">${i18n.t('create_account')}</span>
              <div class="loading-dots hidden" id="register-loading">
                <span></span><span></span><span></span>
              </div>
            </button>
          </form>

          <div class="auth-footer">
            <p class="text-secondary text-sm">
              ${i18n.t('have_account')}
              <a href="#/login" class="auth-link font-semibold">${i18n.t('login')}</a>
            </p>
          </div>
        </div>
      </div>
    `;
  },

  mount() {
    const form = document.getElementById('register-form');
    const backBtn = document.getElementById('back-btn');
    const togglePwdBtn = document.getElementById('toggle-reg-pwd');
    const pwdInput = document.getElementById('reg-password');

    backBtn?.addEventListener('click', () => router.back());

    togglePwdBtn?.addEventListener('click', () => {
      pwdInput.type = pwdInput.type === 'password' ? 'text' : 'password';
    });

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleRegister();
    });
  },

  async handleRegister() {
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const phone = document.getElementById('reg-phone').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm-password').value;

    // Validation
    let hasError = false;

    if (!name || name.length < 2) {
      this.showError('name', i18n.t('required'));
      hasError = true;
    } else this.clearError('name');

    if (!email || !email.includes('@')) {
      this.showError('reg-email', i18n.t('invalid_email'));
      hasError = true;
    } else this.clearError('reg-email');

    if (!phone) {
      this.showError('reg-phone', i18n.t('phone_required'));
      hasError = true;
    } else if (!/^\+?[0-9]{8,15}$/.test(phone.replace(/\s/g, ''))) {
      this.showError('reg-phone', i18n.t('invalid_phone'));
      hasError = true;
    } else this.clearError('reg-phone');

    if (!password || password.length < 8) {
      this.showError('reg-password', i18n.t('password_min'));
      hasError = true;
    } else this.clearError('reg-password');

    if (password !== confirmPassword) {
      this.showError('confirm-password', i18n.t('passwords_mismatch'));
      hasError = true;
    } else this.clearError('confirm-password');

    if (hasError) return;

    this.setLoading(true);

    try {
      await api.register({
        email,
        password,
        full_name: name,
        phone: phone.replace(/\s/g, ''),
        language: i18n.lang,
      });

      // Account is created PENDING admin approval — no auto-login.
      toast.success(i18n.t('register_pending'));
      router.navigate('/login');
    } catch (error) {
      toast.error(error.message || i18n.t('error_generic'));
    } finally {
      this.setLoading(false);
    }
  },

  showError(field, message) {
    const el = document.getElementById(`${field}-error`);
    const fieldEl = document.getElementById(`${field}-field`);
    if (el) { el.textContent = message; el.classList.remove('hidden'); }
    fieldEl?.classList.add('error');
  },

  clearError(field) {
    document.getElementById(`${field}-error`)?.classList.add('hidden');
    document.getElementById(`${field}-field`)?.classList.remove('error');
  },

  setLoading(loading) {
    const btn = document.getElementById('register-btn');
    const text = document.getElementById('register-btn-text');
    const spinner = document.getElementById('register-loading');
    if (btn) btn.disabled = loading;
    text?.classList.toggle('hidden', loading);
    spinner?.classList.toggle('hidden', !loading);
  },

  unmount() {}
};

export default RegisterPage;
