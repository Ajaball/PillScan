/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Medications Page
   List, add, and manage user medications
   ═══════════════════════════════════════════════════════════════════ */
import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const MedicationsPage = {
  render() {
    return `
      <div class="page-header">
        <h1 class="page-title">${i18n.t('my_medications')}</h1>
        <button class="btn btn-icon btn-primary" id="add-med-fab" aria-label="${i18n.t('add_medication')}">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
      </div>
      <div class="page-content" id="meds-container">
        <div class="skeleton skeleton-card mb-3"></div>
        <div class="skeleton skeleton-card mb-3"></div>
        <div class="skeleton skeleton-card mb-3"></div>
      </div>
    `;
  },

  async mount(params) {
    document.getElementById('add-med-fab')?.addEventListener('click', () => this.showAddModal());
    await this.loadMedications();

    if (params?.addDrugId) {
      this.showAddModal(params.addDrugId);
    }
  },

  async loadMedications() {
    const container = document.getElementById('meds-container');
    if (!container) return;
    try {
      const meds = await api.getMedications(false);
      if (!meds || meds.length === 0) {
        container.innerHTML = `
          <div class="empty-state" style="padding-top:20%;">
            <div class="text-5xl mb-4">💊</div>
            <h3 class="font-semibold mb-2">${i18n.t('no_medications')}</h3>
            <p class="text-secondary text-sm mb-4">${i18n.t('add_first_med')}</p>
            <button class="btn btn-primary" id="empty-add-btn">${i18n.t('add_medication')}</button>
          </div>
        `;
        document.getElementById('empty-add-btn')?.addEventListener('click', () => this.showAddModal());
        return;
      }
      container.innerHTML = `<div class="stagger-children">${meds.map(med => this.renderMedCard(med)).join('')}</div>`;
      container.querySelectorAll('.med-delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => { e.stopPropagation(); this.deleteMedication(btn.dataset.id); });
      });
      container.querySelectorAll('.med-card-link').forEach(el => {
        el.addEventListener('click', () => {
          if (el.dataset.drugId) router.navigate('/drug/:id', { id: el.dataset.drugId });
        });
      });
    } catch (error) {
      container.innerHTML = `<div class="empty-state"><p class="text-secondary">${i18n.t('error_generic')}</p></div>`;
    }
  },

  renderMedCard(med) {
    const name = i18n.lang === 'ar' ? (med.drug_name_ar || med.custom_name || med.drug_name_en || '-') : (med.drug_name_en || med.custom_name || '-');
    return `
      <div class="card card-interactive animate-fade-in-up mb-3 med-card-link" data-drug-id="${med.drug_id || ''}">
        <div class="flex items-center gap-3">
          <div class="avatar avatar-md" style="background:${med.is_active ? 'var(--color-primary-gradient)' : 'var(--color-bg-tertiary)'};">💊</div>
          <div class="flex-1">
            <h4 class="font-semibold">${name}</h4>
            <p class="text-xs text-secondary">${med.dosage || ''} ${med.frequency ? '• ' + med.frequency : ''}</p>
          </div>
          <span class="badge ${med.is_active ? 'badge-success' : 'badge-warning'}">${med.is_active ? i18n.t('active') : i18n.t('inactive')}</span>
          <button class="btn btn-icon-sm btn-ghost med-delete-btn" data-id="${med.id}">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-error)" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </div>
    `;
  },

  showAddModal(drugId = null) {
    const overlay = document.createElement('div');
    overlay.className = 'bottom-sheet-overlay';
    overlay.id = 'add-med-overlay';

    const sheet = document.createElement('div');
    sheet.className = 'bottom-sheet';
    sheet.innerHTML = `
      <div class="bottom-sheet-handle"></div>
      <h2 class="text-lg font-bold mb-4">${i18n.t('add_medication')}</h2>
      <form id="add-med-form">
        <div class="input-group mb-3">
          <label class="input-label">${i18n.t('custom_name')} *</label>
          <div class="input-field"><input type="text" id="med-name" placeholder="${i18n.t('medication_name')}" required></div>
        </div>
        <div class="input-group mb-3">
          <label class="input-label">${i18n.t('dosage')}</label>
          <div class="input-field"><input type="text" id="med-dosage" placeholder="500mg"></div>
        </div>
        <div class="input-group mb-3">
          <label class="input-label">${i18n.t('frequency')}</label>
          <div class="input-field">
            <select id="med-frequency" style="color:var(--color-text-primary);background:transparent;">
              <option value="daily">${i18n.t('frequency_daily')}</option>
              <option value="twice_daily">${i18n.t('frequency_twice')}</option>
              <option value="three_times_daily">${i18n.t('frequency_three')}</option>
              <option value="weekly">${i18n.t('frequency_weekly')}</option>
              <option value="custom">${i18n.t('frequency_custom')}</option>
            </select>
          </div>
        </div>
        <div class="input-group mb-3">
          <label class="input-label">${i18n.t('notes')} <span class="text-tertiary text-xs">(${i18n.t('optional')})</span></label>
          <div class="input-field"><input type="text" id="med-notes" placeholder="${i18n.t('notes')}"></div>
        </div>
        <div class="flex gap-3 mt-4">
          <button type="button" class="btn btn-secondary flex-1" id="cancel-add-med">${i18n.t('cancel')}</button>
          <button type="submit" class="btn btn-primary flex-1">${i18n.t('save')}</button>
        </div>
      </form>
    `;

    document.body.appendChild(overlay);
    document.body.appendChild(sheet);

    const close = () => {
      overlay.classList.add('closing');
      sheet.classList.add('closing');
      setTimeout(() => { overlay.remove(); sheet.remove(); }, 300);
    };

    overlay.addEventListener('click', close);
    document.getElementById('cancel-add-med')?.addEventListener('click', close);

    document.getElementById('add-med-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = {
        custom_name: document.getElementById('med-name').value.trim(),
        dosage: document.getElementById('med-dosage').value.trim() || undefined,
        frequency: document.getElementById('med-frequency').value,
        notes: document.getElementById('med-notes').value.trim() || undefined,
        drug_id: drugId || undefined,
      };
      if (!data.custom_name && !data.drug_id) { toast.warning(i18n.t('required')); return; }
      try {
        await api.createMedication(data);
        toast.success(i18n.t('success'));
        close();
        this.loadMedications();
      } catch (err) {
        toast.error(err.message || i18n.t('error_generic'));
      }
    });
  },

  async deleteMedication(id) {
    if (!confirm(i18n.t('delete_medication'))) return;
    try {
      await api.deleteMedication(id);
      toast.success(i18n.t('success'));
      this.loadMedications();
    } catch (err) { toast.error(err.message); }
  },

  unmount() {
    document.getElementById('add-med-overlay')?.remove();
    document.querySelector('.bottom-sheet')?.remove();
  }
};

export default MedicationsPage;
