/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Pharmacist Assistant
   Type a drug name → Gemini → structured Arabic drug info in cards.
   A persistent medical-disclaimer banner sits above every result.
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';

const DrugAssistantPage = {
  render() {
    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('assistant_title')}</h1>
        <div style="width:48px;"></div>
      </div>
      <div class="page-content">
        <!-- Persistent medical disclaimer -->
        <div class="card mb-4" style="border:1px solid var(--color-warning);background:color-mix(in srgb, var(--color-warning) 12%, transparent);">
          <div class="flex items-start gap-2">
            <span style="font-size:18px;line-height:1;">⚠️</span>
            <p class="text-xs" style="color:var(--color-warning);">${i18n.t('assistant_disclaimer')}</p>
          </div>
        </div>

        <form id="assistant-form" novalidate>
          <div class="input-field mb-3">
            <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input type="search" id="assistant-input" placeholder="${i18n.t('assistant_placeholder')}" autofocus>
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="assistant-btn">
            <span id="assistant-btn-text">${i18n.t('search')}</span>
            <div class="loading-dots hidden" id="assistant-loading"><span></span><span></span><span></span></div>
          </button>
        </form>

        <div id="assistant-results" class="mt-4">
          <p class="text-center text-secondary text-sm mt-8">${i18n.t('assistant_empty')}</p>
        </div>
      </div>
    `;
  },

  mount(params = {}) {
    document.getElementById('back-btn')?.addEventListener('click', () => router.back());

    const form = document.getElementById('assistant-form');
    const input = document.getElementById('assistant-input');
    form?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.doSearch(input.value.trim());
    });

    // Prefill + auto-run when navigated with a drug name (e.g. from search).
    const prefill = params.name || router.getParams().name;
    if (prefill) {
      input.value = prefill;
      this.doSearch(prefill);
    }
  },

  setLoading(loading) {
    const btn = document.getElementById('assistant-btn');
    const text = document.getElementById('assistant-btn-text');
    const spinner = document.getElementById('assistant-loading');
    if (btn) btn.disabled = loading;
    text?.classList.toggle('hidden', loading);
    spinner?.classList.toggle('hidden', !loading);
  },

  async doSearch(name) {
    const container = document.getElementById('assistant-results');
    if (!container || !name) return;

    this.setLoading(true);
    container.innerHTML = `
      <div class="card text-center" style="padding:var(--space-6);">
        <div class="loading-dots" style="justify-content:center;"><span></span><span></span><span></span></div>
        <p class="text-secondary text-sm mt-3">${i18n.t('assistant_loading')}</p>
      </div>`;

    try {
      const info = await api.getDrugInfo(name);
      this.renderResult(container, info);
    } catch (err) {
      container.innerHTML = `<div class="empty-state mt-6"><div class="text-4xl mb-2">⚠️</div><p class="text-secondary text-sm">${err.message || i18n.t('error_generic')}</p></div>`;
    } finally {
      this.setLoading(false);
    }
  },

  esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
  },

  listCard(title, items) {
    if (!items || !items.length) return '';
    return `
      <div class="card mb-3 animate-fade-in-up">
        <h4 class="font-semibold text-sm mb-2">${title}</h4>
        <ul style="list-style:disc;padding-inline-start:20px;margin:0;">
          ${items.map(it => `<li class="text-sm text-secondary mb-1">${this.esc(it)}</li>`).join('')}
        </ul>
      </div>`;
  },

  renderResult(container, info) {
    // Not configured — prompt to add a Gemini key.
    if (info.is_configured === false) {
      container.innerHTML = `
        <div class="empty-state mt-6">
          <div class="text-4xl mb-2">🔑</div>
          <p class="text-secondary text-sm mb-3">${i18n.t('assistant_not_configured')}</p>
          <button class="btn btn-primary btn-sm" id="go-ai-settings">${i18n.t('ai_settings')}</button>
        </div>`;
      document.getElementById('go-ai-settings')?.addEventListener('click', () => router.navigate('/ai-settings'));
      return;
    }

    // Not recognized — clear message, no fabricated content.
    if (!info.recognized) {
      container.innerHTML = `
        <div class="empty-state mt-6">
          <div class="text-4xl mb-2">🤔</div>
          <p class="text-secondary text-sm">${i18n.t('assistant_not_recognized')}</p>
          ${info.message ? `<p class="text-xs text-tertiary mt-2">${this.esc(info.message)}</p>` : ''}
        </div>`;
      return;
    }

    // Fixed three-field layout, always in this order:
    // 1) اسم الدواء  2) الأعراض الجانبية  3) مواعيد الاستخدام
    container.innerHTML = `
      <div class="card card-glow mb-3 animate-fade-in-up">
        <div class="flex items-center gap-3">
          <div class="avatar avatar-md" style="background:var(--color-primary-gradient);">💊</div>
          <h3 class="font-bold text-base">${this.esc(info.name)}</h3>
        </div>
      </div>
      ${this.listCard(i18n.t('assistant_side_effects'), info.sideEffects)}
      ${this.listCard(i18n.t('assistant_usage_times'), info.usageTimes)}
    `;
  },

  unmount() {},
};

export default DrugAssistantPage;
