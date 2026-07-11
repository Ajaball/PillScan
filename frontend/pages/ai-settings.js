/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — AI Settings Page
   Let the user add their own Gemini / OpenAI (ChatGPT) API keys used by
   the leaflet summarizer, and choose which provider to use.
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const AISettingsPage = {
  // Current server-side status (which providers are configured). Loaded on mount.
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

  /** Small "Configured / Not set" badge */
  statusBadge(configured, hint) {
    if (configured) {
      const hintTxt = hint ? ` <span dir="ltr" class="text-tertiary">${hint}</span>` : '';
      return `<span class="badge badge-success">✓ ${i18n.t('ai_key_configured')}</span>${hintTxt}`;
    }
    return `<span class="badge badge-muted">${i18n.t('ai_key_not_configured')}</span>`;
  },

  /** Provider option card (radio) */
  providerOption(value, label, checked) {
    return `
      <label class="ai-provider-option ${checked ? 'selected' : ''}">
        <input type="radio" name="ai-provider" value="${value}" ${checked ? 'checked' : ''}>
        <span class="ai-provider-label">${label}</span>
        <span class="ai-provider-check">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
        </span>
      </label>`;
  },

  formHtml() {
    const s = this.status || {};
    const provider = s.llm_provider || 'gemini';

    return `
      <p class="text-sm text-secondary mb-4">${i18n.t('ai_settings_intro')}</p>

      <!-- Provider selector -->
      <div class="card animate-fade-in-up mb-4">
        <h3 class="font-semibold mb-3">${i18n.t('ai_provider')}</h3>
        <div class="ai-provider-group">
          ${this.providerOption('gemini', i18n.t('ai_provider_gemini'), provider === 'gemini')}
          ${this.providerOption('openai', i18n.t('ai_provider_openai'), provider === 'openai')}
        </div>
      </div>

      <!-- Gemini key -->
      <div class="card animate-fade-in-up mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold">${i18n.t('ai_gemini_key')}</h3>
          <span id="gemini-status">${this.statusBadge(s.gemini_configured, s.gemini_key_hint)}</span>
        </div>
        <div class="input-field">
          <input type="password" id="gemini-key-input" placeholder="${i18n.t('ai_key_placeholder')}" autocomplete="off" dir="ltr">
          <button type="button" class="input-action" id="gemini-toggle" aria-label="toggle">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
        </div>
        <div class="flex items-center justify-between mt-2">
          <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener" class="auth-link text-xs">${i18n.t('ai_get_gemini_key')}</a>
          ${s.gemini_configured ? `<button class="btn btn-ghost btn-sm" id="gemini-clear" style="color:var(--color-error);">${i18n.t('ai_clear_key')}</button>` : ''}
        </div>
      </div>

      <!-- OpenAI key -->
      <div class="card animate-fade-in-up mb-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="font-semibold">${i18n.t('ai_openai_key')}</h3>
          <span id="openai-status">${this.statusBadge(s.openai_configured, s.openai_key_hint)}</span>
        </div>
        <div class="input-field">
          <input type="password" id="openai-key-input" placeholder="${i18n.t('ai_key_placeholder')}" autocomplete="off" dir="ltr">
          <button type="button" class="input-action" id="openai-toggle" aria-label="toggle">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
        </div>
        <div class="flex items-center justify-between mt-2">
          <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener" class="auth-link text-xs">${i18n.t('ai_get_openai_key')}</a>
          ${s.openai_configured ? `<button class="btn btn-ghost btn-sm" id="openai-clear" style="color:var(--color-error);">${i18n.t('ai_clear_key')}</button>` : ''}
        </div>
      </div>

      <button class="btn btn-primary btn-lg btn-block mt-2" id="ai-save-btn">
        <span id="ai-save-text">${i18n.t('save')}</span>
        <div class="loading-dots hidden" id="ai-save-loading"><span></span><span></span><span></span></div>
      </button>
    `;
  },

  bindForm() {
    // Provider option highlight
    document.querySelectorAll('.ai-provider-option input').forEach(input => {
      input.addEventListener('change', () => {
        document.querySelectorAll('.ai-provider-option').forEach(opt => {
          opt.classList.toggle('selected', opt.querySelector('input').checked);
        });
      });
    });

    // Show/hide key toggles
    this.bindToggle('gemini-toggle', 'gemini-key-input');
    this.bindToggle('openai-toggle', 'openai-key-input');

    // Clear buttons
    document.getElementById('gemini-clear')?.addEventListener('click', () => this.clearKey('gemini'));
    document.getElementById('openai-clear')?.addEventListener('click', () => this.clearKey('openai'));

    // Save
    document.getElementById('ai-save-btn')?.addEventListener('click', () => this.save());
  },

  bindToggle(btnId, inputId) {
    document.getElementById(btnId)?.addEventListener('click', () => {
      const input = document.getElementById(inputId);
      if (input) input.type = input.type === 'password' ? 'text' : 'password';
    });
  },

  selectedProvider() {
    return document.querySelector('.ai-provider-option input:checked')?.value || 'gemini';
  },

  async clearKey(provider) {
    try {
      const field = provider === 'openai' ? 'openai_api_key' : 'gemini_api_key';
      this.status = await api.updateAISettings({ [field]: '' });
      toast.success(i18n.t('ai_key_cleared'));
      document.getElementById('ai-settings-container').innerHTML = this.formHtml();
      this.bindForm();
    } catch (error) {
      toast.error(error.message || i18n.t('error_generic'));
    }
  },

  async save() {
    const geminiKey = document.getElementById('gemini-key-input')?.value.trim();
    const openaiKey = document.getElementById('openai-key-input')?.value.trim();
    const provider = this.selectedProvider();

    const payload = { llm_provider: provider };
    if (geminiKey) payload.gemini_api_key = geminiKey;
    if (openaiKey) payload.openai_api_key = openaiKey;

    // Nothing to change if provider is unchanged and no new keys entered
    const providerUnchanged = this.status && this.status.llm_provider === provider;
    if (providerUnchanged && !geminiKey && !openaiKey) {
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
