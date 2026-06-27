/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Reminders Page
   ═══════════════════════════════════════════════════════════════════ */
import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const RemindersPage = {
  render() {
    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('reminders')}</h1>
        <div style="width:48px;"></div>
      </div>
      <div class="page-content no-navbar" id="reminders-container">
        <div class="skeleton skeleton-card mb-3"></div>
        <div class="skeleton skeleton-card mb-3"></div>
      </div>
    `;
  },

  async mount() {
    document.getElementById('back-btn')?.addEventListener('click', () => router.back());
    await this.loadReminders();
  },

  async loadReminders() {
    const container = document.getElementById('reminders-container');
    if (!container) return;
    try {
      const reminders = await api.getReminders();
      if (!reminders || reminders.length === 0) {
        container.innerHTML = `
          <div class="empty-state" style="padding-top:20%;">
            <div class="text-5xl mb-4">⏰</div>
            <h3 class="font-semibold mb-2">${i18n.t('no_reminders')}</h3>
            <p class="text-secondary text-sm">${i18n.t('add_reminder')}</p>
          </div>
        `;
        return;
      }
      container.innerHTML = `<div class="stagger-children">${reminders.map(r => `
        <div class="card animate-fade-in-up mb-3">
          <div class="flex items-center gap-3">
            <div class="reminder-time-badge">
              <span class="text-lg font-bold">${r.reminder_time ? r.reminder_time.slice(0,5) : '--:--'}</span>
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-sm">${r.medication_name || r.notification_title || '-'}</h4>
              <p class="text-xs text-secondary">${(r.days_of_week || []).map(d => i18n.t('day_' + d.toLowerCase().slice(0,3))).join(', ') || i18n.t('frequency_daily')}</p>
            </div>
            <label class="toggle">
              <input type="checkbox" ${r.is_active ? 'checked' : ''} data-id="${r.id}" class="reminder-toggle">
              <span class="toggle-track"></span>
            </label>
          </div>
        </div>
      `).join('')}</div>`;

      container.querySelectorAll('.reminder-toggle').forEach(toggle => {
        toggle.addEventListener('change', async (e) => {
          try {
            await api.updateReminder(e.target.dataset.id, { is_active: e.target.checked });
            toast.success(e.target.checked ? i18n.t('reminder_enabled') : i18n.t('reminder_disabled'));
          } catch(err) { toast.error(err.message); }
        });
      });
    } catch {
      container.innerHTML = `<div class="empty-state"><p class="text-secondary">${i18n.t('error_generic')}</p></div>`;
    }
  },

  unmount() {}
};

export default RemindersPage;
