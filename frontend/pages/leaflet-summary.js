/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Leaflet Summary Page
   Shows the AI-generated Arabic summary of a scanned leaflet/prescription
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import storage from '../js/storage.js';

const LeafletSummaryPage = {
  render() {
    const result = storage.get('last_leaflet_summary');

    if (!result || !result.summary) {
      return `
        <div class="page-header">
          <button class="btn btn-icon btn-secondary" id="leaflet-summary-back">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
          </button>
          <h1 class="page-title">${i18n.t('leaflet_summary_title')}</h1>
          <div style="width:48px;"></div>
        </div>
        <div class="page-content no-navbar" style="display:flex;align-items:center;justify-content:center;">
          <div class="empty-state">
            <div class="text-4xl mb-4">📄</div>
            <p class="text-secondary">${i18n.t('leaflet_no_summary')}</p>
            <button class="btn btn-primary mt-4" id="leaflet-new-scan">${i18n.t('leaflet_new_scan')}</button>
          </div>
        </div>
      `;
    }

    const imageUrl = result._local_image || '';
    const notConfigured = result.is_configured === false;
    const disclaimer = i18n.lang === 'ar' ? result.disclaimer_ar : result.disclaimer_en;
    const providerLabel = (result.provider === 'openai' ? 'ChatGPT' : 'Gemini');

    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="leaflet-summary-back">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('leaflet_summary_title')}</h1>
        <div style="width:48px;"></div>
      </div>

      <div class="page-content no-navbar stagger-children">

        <!-- ── Scanned Leaflet Image ── -->
        ${imageUrl ? `
          <div style="margin-bottom:20px; border-radius:16px; overflow:hidden; background:#0a0a12;">
            <img src="${imageUrl}" alt="Scanned leaflet"
                 style="width:100%; max-height:280px; object-fit:contain; display:block;"
                 onerror="this.parentElement.style.display='none';" />
          </div>
        ` : ''}

        ${notConfigured ? `
          <div class="card animate-fade-in-up" style="border-left:4px solid var(--color-warning);">
            <div class="leaflet-summary-body">${this.formatSummary(result.summary)}</div>
          </div>
        ` : `
          <!-- ── AI Summary Card ── -->
          <div class="card card-glow animate-fade-in-up" style="border-left:4px solid var(--color-primary);">
            <div class="flex items-center gap-2 mb-3">
              <span class="badge badge-primary">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="vertical-align:middle;"><path d="M12 2l2.09 6.26L20 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
                ${i18n.t('leaflet_ai_summary')}
              </span>
              <span class="text-xs text-tertiary">${providerLabel}</span>
            </div>
            <div class="leaflet-summary-body">${this.formatSummary(result.summary)}</div>
          </div>
        `}

        <!-- ── Disclaimer ── -->
        <div class="card mt-4" style="background:var(--color-warning-soft, rgba(245,158,11,0.08)); border:1px solid rgba(245,158,11,0.25);">
          <div class="flex gap-2 items-start">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-warning)" stroke-width="2" stroke-linecap="round" style="flex-shrink:0;margin-top:2px;"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            <p class="text-xs text-secondary" style="line-height:1.6;">${disclaimer}</p>
          </div>
        </div>

        <!-- ── New Scan Button ── -->
        <div class="mt-6 mb-4">
          <button class="btn btn-secondary btn-block" id="leaflet-new-scan">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/></svg>
            ${i18n.t('leaflet_new_scan')}
          </button>
        </div>
      </div>
    `;
  },

  /**
   * Render the summary text as safe HTML.
   * Escapes everything first, then applies a tiny markdown subset:
   * headings (#), bullets (•/-/*), and **bold**.
   */
  formatSummary(text) {
    const escape = (s) => s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    const inline = (s) => escape(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    const lines = (text || '').split('\n');
    let html = '';
    let inList = false;

    const closeList = () => {
      if (inList) { html += '</ul>'; inList = false; }
    };

    for (const raw of lines) {
      const line = raw.trim();
      if (!line) { closeList(); continue; }

      const heading = line.match(/^#{1,6}\s+(.*)$/);
      const bullet = line.match(/^[•\-*]\s+(.*)$/);

      if (heading) {
        closeList();
        html += `<h4 class="leaflet-summary-heading">${inline(heading[1])}</h4>`;
      } else if (bullet) {
        if (!inList) { html += '<ul class="leaflet-summary-list">'; inList = true; }
        html += `<li>${inline(bullet[1])}</li>`;
      } else {
        closeList();
        html += `<p class="leaflet-summary-para">${inline(line)}</p>`;
      }
    }
    closeList();
    return html || `<p class="leaflet-summary-para">${escape(text || '')}</p>`;
  },

  mount() {
    document.getElementById('leaflet-summary-back')?.addEventListener('click', () => router.navigate('/home'));
    document.getElementById('leaflet-new-scan')?.addEventListener('click', () => router.navigate('/leaflet-scanner'));
  },

  unmount() {}
};

export default LeafletSummaryPage;
