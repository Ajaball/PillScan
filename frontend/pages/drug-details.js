/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Drug Details Page
   Comprehensive drug information display
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const DrugDetailsPage = {
  render() {
    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('drug_details')}</h1>
        <div style="width:48px;"></div>
      </div>
      <div class="page-content no-navbar" id="drug-content">
        <div class="skeleton skeleton-card mb-4" style="height:120px;"></div>
        <div class="skeleton skeleton-text" style="width:70%;"></div>
        <div class="skeleton skeleton-text" style="width:50%;"></div>
        <div class="skeleton skeleton-card mt-4" style="height:80px;"></div>
      </div>
    `;
  },

  async mount(params) {
    document.getElementById('back-btn')?.addEventListener('click', () => router.back());

    const drugId = params?.id || router.getHashParam('id');
    if (!drugId) {
      router.navigate('/home');
      return;
    }

    await this.loadDrug(drugId);
  },

  async loadDrug(drugId) {
    const container = document.getElementById('drug-content');
    if (!container) return;

    try {
      const drug = await api.getDrug(drugId);
      const isAr = i18n.lang === 'ar';

      container.innerHTML = `
        <div class="stagger-children">
          <!-- Drug Name Card -->
          <div class="card card-glow animate-fade-in-up drug-name-card">
            <div class="flex items-center gap-3">
              <div class="drug-icon">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5">
                  <path d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3"/>
                </svg>
              </div>
              <div class="flex-1">
                <h2 class="text-xl font-bold">${isAr ? (drug.name_ar || drug.name_en) : drug.name_en}</h2>
                <p class="text-sm text-tertiary">${isAr ? drug.name_en : (drug.name_ar || '')}</p>
              </div>
            </div>
            <div class="flex flex-wrap gap-2 mt-3">
              <span class="badge badge-primary">${drug.dosage_form || ''}</span>
              <span class="badge badge-primary">${drug.strength || ''}</span>
              ${drug.requires_prescription
                ? `<span class="badge badge-warning">⚕️ ${i18n.t('requires_prescription')}</span>`
                : `<span class="badge badge-success">✓ ${i18n.t('otc')}</span>`
              }
            </div>
          </div>

          <!-- Generic Name -->
          <div class="card animate-fade-in-up mt-3">
            <h3 class="text-sm font-semibold text-secondary mb-2">${i18n.t('generic_name')}</h3>
            <p class="font-medium">${isAr ? (drug.generic_name_ar || drug.generic_name_en || '-') : (drug.generic_name_en || '-')}</p>
            ${drug.generic_name_en && isAr ? `<p class="text-sm text-tertiary">${drug.generic_name_en}</p>` : ''}
          </div>

          <!-- Quick Info Grid -->
          <div class="grid grid-2 gap-3 mt-3">
            <div class="card animate-fade-in-up">
              <p class="text-xs text-secondary">${i18n.t('pill_shape')}</p>
              <p class="font-semibold mt-1">${this.getShapeIcon(drug.shape)} ${drug.shape || '-'}</p>
            </div>
            <div class="card animate-fade-in-up">
              <p class="text-xs text-secondary">${i18n.t('pill_color')}</p>
              <p class="font-semibold mt-1">
                <span class="color-dot" style="background:${this.getColorHex(drug.color)};"></span>
                ${drug.color || '-'}
              </p>
            </div>
          </div>

          <!-- Description -->
          ${drug.description_en || drug.description_ar ? `
            <div class="card animate-fade-in-up mt-3">
              <h3 class="text-sm font-semibold text-secondary mb-2">${i18n.t('description')}</h3>
              <p class="text-sm leading-relaxed">${isAr ? (drug.description_ar || drug.description_en) : (drug.description_en || drug.description_ar)}</p>
            </div>
          ` : ''}

          <!-- Usage Instructions -->
          ${drug.usage_instructions_en || drug.usage_instructions_ar ? `
            <div class="card animate-fade-in-up mt-3">
              <h3 class="text-sm font-semibold text-secondary mb-2">📋 ${i18n.t('usage_instructions')}</h3>
              <p class="text-sm leading-relaxed">${isAr ? (drug.usage_instructions_ar || drug.usage_instructions_en) : (drug.usage_instructions_en || drug.usage_instructions_ar)}</p>
            </div>
          ` : ''}

          <!-- Side Effects -->
          ${drug.side_effects && drug.side_effects.length > 0 ? `
            <div class="card animate-fade-in-up mt-3">
              <h3 class="text-sm font-semibold text-secondary mb-3">⚠️ ${i18n.t('side_effects')}</h3>
              <div class="side-effects-list">
                ${drug.side_effects.map(se => `
                  <div class="side-effect-item">
                    <span class="badge badge-${this.getSeverityBadge(se.severity)}">${i18n.t('severity_' + se.severity)}</span>
                    <span class="text-sm">${isAr ? (se.effect_ar || se.effect_en) : (se.effect_en || se.effect_ar)}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <!-- Contraindications -->
          ${drug.contraindications && drug.contraindications.length > 0 ? `
            <div class="card animate-fade-in-up mt-3" style="border-color: rgba(239,68,68,0.2);">
              <h3 class="text-sm font-semibold text-error mb-3">🚫 ${i18n.t('contraindications')}</h3>
              <ul class="contra-list">
                ${drug.contraindications.map(ci => `
                  <li class="text-sm">
                    ${isAr ? (ci.contraindication_ar || ci.contraindication_en) : (ci.contraindication_en || ci.contraindication_ar)}
                  </li>
                `).join('')}
              </ul>
            </div>
          ` : ''}

          <!-- Storage -->
          ${drug.storage_instructions ? `
            <div class="card animate-fade-in-up mt-3">
              <h3 class="text-sm font-semibold text-secondary mb-2">🌡️ ${i18n.t('storage')}</h3>
              <p class="text-sm">${drug.storage_instructions}</p>
            </div>
          ` : ''}

          <!-- Manufacturer -->
          ${drug.manufacturer ? `
            <div class="card animate-fade-in-up mt-3">
              <h3 class="text-sm font-semibold text-secondary mb-2">🏭 ${i18n.t('manufacturer')}</h3>
              <p class="text-sm font-medium">${drug.manufacturer}</p>
            </div>
          ` : ''}

          <!-- Add to medications button -->
          <button class="btn btn-primary btn-block btn-lg mt-6 mb-4" id="add-to-meds-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
            ${i18n.t('add_to_meds')}
          </button>
        </div>
      `;

      // Event listeners
      document.getElementById('add-to-meds-btn')?.addEventListener('click', () => {
        router.navigate('/medications', { addDrugId: drugId });
      });

    } catch (error) {
      container.innerHTML = `
        <div class="empty-state" style="padding-top:30%;">
          <div class="text-4xl mb-4">❌</div>
          <p class="text-secondary">${error.message || i18n.t('error_generic')}</p>
          <button class="btn btn-primary mt-4" onclick="location.reload()">${i18n.t('retry')}</button>
        </div>
      `;
    }
  },

  getShapeIcon(shape) {
    const icons = { round: '⚪', oval: '🥚', capsule: '💊', tablet: '⬜', heart: '❤️' };
    return icons[shape] || '💊';
  },

  getColorHex(color) {
    const map = { white: '#f1f5f9', pink: '#f472b6', red: '#ef4444', yellow: '#fbbf24', blue: '#3b82f6', green: '#22c55e', purple: '#a855f7', orange: '#fb923c' };
    return map[color?.toLowerCase()] || '#94a3b8';
  },

  getSeverityBadge(severity) {
    if (severity === 'mild') return 'success';
    if (severity === 'moderate') return 'warning';
    return 'error';
  },

  unmount() {}
};

export default DrugDetailsPage;
