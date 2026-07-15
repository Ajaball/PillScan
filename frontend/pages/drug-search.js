/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Drug Search Page
   ═══════════════════════════════════════════════════════════════════ */
import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';

const DrugSearchPage = {
  searchTimeout: null,
  render() {
    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('search_drugs')}</h1>
        <div style="width:48px;"></div>
      </div>
      <div class="page-content">
        <div class="input-field mb-4">
          <svg class="input-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="search" id="search-input" placeholder="${i18n.t('search_placeholder')}" autofocus>
        </div>
        <div id="search-results">
          <p class="text-center text-secondary text-sm mt-8">${i18n.t('search_placeholder')}</p>
        </div>
      </div>
    `;
  },

  mount() {
    document.getElementById('back-btn')?.addEventListener('click', () => router.back());

    const input = document.getElementById('search-input');
    input?.addEventListener('input', () => {
      clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(() => this.doSearch(input.value.trim()), 300);
    });
  },

  async doSearch(query) {
    const container = document.getElementById('search-results');
    if (!container) return;
    if (!query) { container.innerHTML = `<p class="text-center text-secondary text-sm mt-8">${i18n.t('search_placeholder')}</p>`; return; }

    container.innerHTML = '<div class="skeleton skeleton-card mb-3"></div><div class="skeleton skeleton-card mb-3"></div>';

    try {
      const drugs = await api.searchDrugs(query);
      const assistantCta = `
        <div class="card card-interactive mt-4 assistant-cta">
          <div class="flex items-center gap-3">
            <div class="avatar avatar-md" style="background:var(--color-primary-gradient);">🤖</div>
            <div class="flex-1">
              <h4 class="font-semibold text-sm">${i18n.t('assistant_ask_about')}</h4>
              <p class="text-xs text-tertiary">${query}</p>
            </div>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}"/></svg>
          </div>
        </div>`;
      const wireAssistant = () => {
        container.querySelector('.assistant-cta')?.addEventListener('click', () =>
          router.navigate('/drug-assistant', { name: query }));
      };

      if (!drugs || drugs.length === 0) {
        container.innerHTML = `<div class="empty-state mt-8"><div class="text-4xl mb-3">🔍</div><p class="text-secondary">${i18n.t('no_results_found')}</p></div>${assistantCta}`;
        wireAssistant();
        return;
      }
      container.innerHTML = `<div class="stagger-children">${drugs.map(d => `
        <div class="card card-interactive animate-fade-in-up mb-3 drug-result" data-id="${d.id}">
          <div class="flex items-center gap-3">
            <div class="avatar avatar-md" style="background:var(--color-primary-gradient);">💊</div>
            <div class="flex-1">
              <h4 class="font-semibold text-sm">${i18n.lang === 'ar' ? (d.name_ar || d.name_en) : d.name_en}</h4>
              <p class="text-xs text-tertiary">${d.generic_name_en || ''} • ${d.strength || ''}</p>
            </div>
            <span class="badge badge-primary text-xs">${d.category || ''}</span>
          </div>
        </div>
      `).join('')}</div>${assistantCta}`;

      container.querySelectorAll('.drug-result').forEach(el => {
        el.addEventListener('click', () => router.navigate('/drug/:id', { id: el.dataset.id }));
      });
      wireAssistant();
    } catch {
      container.innerHTML = `<p class="text-center text-secondary">${i18n.t('error_generic')}</p>`;
    }
  },

  unmount() { clearTimeout(this.searchTimeout); }
};

export default DrugSearchPage;
