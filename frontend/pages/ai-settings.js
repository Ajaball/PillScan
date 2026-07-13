/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — AI Settings Page
   Let the user add up to 5 of their own Gemini API keys. The app tries
   them in order and moves to the next automatically when one is exhausted.
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const KEY_SLOTS = 5;

const AISettingsPage = {
  // Current server-side status (which key slots are configured). Loaded on mount.
  status: null,

  render() {
    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="ai-back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('ai_settings')}</h1>
        <div style="width:48px;"></div>
      </div>

      <div class="page-content no-navbar" id="ai-settings-container">
        <div class="skeleton skeleton-card mb-3"></div>
        <div class="skeleton skeleton-card mb-3"></div>
      </div>
    `;
  },

  async mount() {
    document.getElementById('ai-back-btn')?.addEventListener('click', () => router.back());
    await this.load();
  },

  async load() {
    const container = document.getElementById('ai-settings-container');
    try {
      this.status = await api.getAISettings();
      container.innerHTML = this.formHtml();
      this.bindForm();
    } catch (error) {
      container.innerHTML = `
        <div class="card text-center p-4">
          <p class="text-secondary">${error.message || i18n.t('error_generic')}</p>
          <button class="btn btn-primary btn-sm mt-3" id="ai-retry">${i18n.t('retry')}</button>
        </div>`;
      document.getElementById('ai-retry')?.addEventListener('click', () => this.load());
    }
  },

  slotAttr(slot) {
    return slot === 1 ? 'gemini_api_key' : `gemini_api_key_${slot}`;
  },

  /** Small "Configured / Not set" badge */
  statusBadge(configured, hint) {
    if (configured) {
      const hintTxt = hint ? ` <span dir="ltr" class="text-tertiary">${hint}</span>` : '';
      return `<span class="badge badge-success">✓ ${i18n.t('ai_key_configured')}</span>${hintTxt}`;
    }
    return `<span class="badge badge-muted">${i18n.t('ai_key_not_configured')}</span>`;
  },

  /** One Gemini key slot (input + status + clear) */
  keySlotHtml(slot, configured, hint) {
    return `
      <div class="card animate-fade-in-up mb-3">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold">${i18n.t('ai_gemini_key')} ${slot}</h3>
          <span>${this.statusBadge(configured, hint)}</span>
        </div>
        <div class="input-field">
          <input type="password" id="gemini-key-input-${slot}" placeholder="${i18n.t('ai_key_placeholder')}" autocomplete="off" dir="ltr">
          <button type="button" class="input-action" id="gemini-toggle-${slot}" aria-label="toggle">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
        </div>
        <div class="flex items-center justify-end mt-2">
          ${configured ? `<button class="btn btn-ghost btn-sm" id="gemini-clear-${slot}" style="color:var(--color-error);">${i18n.t('ai_clear_key')}</button>` : ''}
        </div>
      </div>`;
  },

  formHtml() {
    const s = this.status || {};
    const keys = s.keys || [];
    const bySlot = (slot) => keys.find(k => k.slot === slot) || { configured: false, hint: null };

    let slotsHtml = '';
    for (let slot = 1; slot <= KEY_SLOTS; slot++) {
      const k = bySlot(slot);
      slotsHtml += this.keySlotHtml(slot, k.configured, k.hint);
    }

    return `
      <p class="text-sm text-secondary mb-3">${i18n.t('ai_settings_intro')}</p>

      <div class="card mb-4" style="background:rgba(99,102,241,0.08); border:1px solid rgba(99,102,241,0.25);">
        <div class="flex gap-2 items-start">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="2" stroke-linecap="round" style="flex-shrink:0;margin-top:2px;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          <p class="text-xs text-secondary" style="line-height:1.6;">${i18n.t('ai_failover_note')}</p>
        </div>
        <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" class="auth-link text-xs" style="display:inline-block;margin-top:8px;">${i18n.t('ai_get_gemini_key')}</a>
      </div>

      ${slotsHtml}

      <button class="btn btn-primary btn-lg btn-block mt-2" id="ai-save-btn">
        <span id="ai-save-text">${i18n.t('save')}</span>
        <div class="loading-dots hidden" id="ai-save-loading"><span></span><span></span><span></span></div>
      </button>

      <button class="btn btn-secondary btn-block mt-3" id="ai-test-btn">
        <span id="ai-test-text">${i18n.t('ai_test_keys')}</span>
        <div class="loading-dots hidden" id="ai-test-loading"><span></span><span></span><span></span></div>
      </button>
      <div id="ai-test-result" class="mt-3"></div>
    `;
  },

  bindForm() {
    for (let slot = 1; slot <= KEY_SLOTS; slot++) {
      this.bindToggle(`gemini-toggle-${slot}`, `gemini-key-input-${slot}`);
      document.getElementById(`gemini-clear-${slot}`)?.addEventListener('click', () => this.clearKey(slot));
    }
    document.getElementById('ai-save-btn')?.addEventListener('click', () => this.save());
    document.getElementById('ai-test-btn')?.addEventListener('click', () => this.testKeys());
  },

  /** Live-test the saved keys and render a per-key status list (mobile-friendly) */
  async testKeys() {
    const btn = document.getElementById('ai-test-btn');
    const text = document.getElementById('ai-test-text');
    const spinner = document.getElementById('ai-test-loading');
    const out = document.getElementById('ai-test-result');
    if (btn) btn.disabled = true;
    text?.classList.add('hidden');
    spinner?.classList.remove('hidden');
    out.innerHTML = '';

    try {
      const d = await api.testAIKeys();
      const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

      if (!d.keys_configured) {
        out.innerHTML = `<div class="card" style="border-left:4px solid var(--color-warning);"><p class="text-sm text-secondary">${esc(d.detail || i18n.t('ai_no_changes'))}</p></div>`;
        return;
      }

      const rows = (d.keys || []).map((k) => {
        const ok = k.ok === true;
        const color = ok ? 'var(--color-success)' : 'var(--color-error)';
        const label = ok ? i18n.t('ai_key_ok') : i18n.t('ai_key_failed');
        const hint = k.hint ? ` <span dir="ltr" class="text-tertiary">${esc(k.hint)}</span>` : '';
        const detail = ok ? '' : `<p class="text-xs text-tertiary mt-1" dir="ltr" style="word-break:break-word;">${esc(k.detail)}</p>`;
        return `
          <div class="flex items-start gap-2 py-2" style="border-bottom:1px solid var(--color-border, rgba(255,255,255,0.08));">
            <span style="color:${color};font-weight:700;">${ok ? '✓' : '✕'}</span>
            <div class="flex-1">
              <div class="text-sm">${i18n.t('ai_gemini_key')} ${k.index}${hint} — <span style="color:${color};">${label}</span></div>
              ${detail}
            </div>
          </div>`;
      }).join('');

      const banner = d.any_key_ok
        ? `<div class="card mb-2" style="border-left:4px solid var(--color-success);"><p class="text-sm">${i18n.t('ai_test_ok')}</p></div>`
        : `<div class="card mb-2" style="border-left:4px solid var(--color-error);"><p class="text-sm">${i18n.t('ai_test_fail')}</p></div>`;

      out.innerHTML = `${banner}<div class="card"><p class="text-xs text-tertiary mb-1">${i18n.t('ai_model')}: <span dir="ltr">${esc(d.model)}</span></p>${rows}</div>`;
    } catch (error) {
      out.innerHTML = `<div class="card" style="border-left:4px solid var(--color-error);"><p class="text-sm text-secondary" dir="ltr" style="word-break:break-word;">${(error.message || i18n.t('error_generic'))}</p></div>`;
    } finally {
      if (btn) btn.disabled = false;
      text?.classList.remove('hidden');
      spinner?.classList.add('hidden');
    }
  },

  bindToggle(btnId, inputId) {
    document.getElementById(btnId)?.addEventListener('click', () => {
      const input = document.getElementById(inputId);
      if (input) input.type = input.type === 'password' ? 'text' : 'password';
    });
  },

  async clearKey(slot) {
    try {
      this.status = await api.updateAISettings({ [this.slotAttr(slot)]: '' });
      toast.success(i18n.t('ai_key_cleared'));
      document.getElementById('ai-settings-container').innerHTML = this.formHtml();
      this.bindForm();
    } catch (error) {
      toast.error(error.message || i18n.t('error_generic'));
    }
  },

  async save() {
    const payload = {};
    for (let slot = 1; slot <= KEY_SLOTS; slot++) {
      const val = document.getElementById(`gemini-key-input-${slot}`)?.value.trim();
      if (val) payload[this.slotAttr(slot)] = val;
    }

    if (Object.keys(payload).length === 0) {
      toast.info(i18n.t('ai_no_changes'));
      return;
    }

    this.setLoading(true);
    try {
      this.status = await api.updateAISettings(payload);
      toast.success(i18n.t('ai_settings_saved'));
      // Re-render so keys clear from inputs and badges refresh
      document.getElementById('ai-settings-container').innerHTML = this.formHtml();
      this.bindForm();
    } catch (error) {
      toast.error(error.message || i18n.t('error_generic'));
    } finally {
      this.setLoading(false);
    }
  },

  setLoading(loading) {
    const btn = document.getElementById('ai-save-btn');
    const text = document.getElementById('ai-save-text');
    const spinner = document.getElementById('ai-save-loading');
    if (btn) btn.disabled = loading;
    text?.classList.toggle('hidden', loading);
    spinner?.classList.toggle('hidden', !loading);
  },

  unmount() {},
};

export default AISettingsPage;
