/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Home Page (Dashboard)
   Shows today's medications, quick scan, and adherence summary
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import storage from '../js/storage.js';
import toast from '../components/toast.js';

const HomePage = {
  render() {
    const user = storage.getUser() || {};
    const greeting = this.getGreeting();
    const firstName = (user.full_name || '').split(' ')[0] || '';

    return `
      <div class="page-header">
        <div>
          <p class="text-secondary text-sm">${greeting}</p>
          <h1 class="text-xl font-bold">${firstName} 👋</h1>
        </div>
        <button class="btn btn-icon btn-secondary" id="search-btn" aria-label="Search">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        </button>
      </div>

      <div class="page-content">
        <!-- Quick Scan Button -->
        <div class="scan-hero card card-glow" id="quick-scan-card">
          <div class="scan-hero-content">
            <div class="scan-hero-text">
              <h2 class="text-lg font-bold">${i18n.t('quick_scan')}</h2>
              <p class="text-sm text-secondary">${i18n.t('scanner_hint')}</p>
            </div>
            <div class="scan-hero-icon animate-breathe">
              <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                <rect x="3" y="3" width="18" height="18" rx="3"/>
                <line x1="3" y1="12" x2="21" y2="12" opacity="0.5"/>
                <path d="M8 7h0M12 7h0M16 7h0M8 17h0M12 17h0M16 17h0" stroke-width="3"/>
              </svg>
            </div>
          </div>
        </div>

        <!-- Leaflet Summary Button -->
        <div class="card card-interactive mt-4" id="leaflet-scan-card">
          <div class="flex items-center gap-3">
            <div class="med-card-icon" style="flex-shrink:0;">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="8" y1="13" x2="16" y2="13"/>
                <line x1="8" y1="17" x2="14" y2="17"/>
              </svg>
            </div>
            <div class="flex-1">
              <h3 class="font-semibold text-sm">${i18n.t('leaflet_card_title')}</h3>
              <p class="text-xs text-secondary">${i18n.t('leaflet_card_desc')}</p>
            </div>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}"/></svg>
          </div>
        </div>

        <!-- Weekly Adherence -->
        <div class="section mt-6">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold">${i18n.t('weekly_adherence')}</h3>
            <a href="#/adherence" class="text-sm text-accent">${i18n.t('nav_history')}</a>
          </div>
          <div class="card" id="adherence-card">
            <div class="adherence-summary" id="adherence-summary">
              <div class="adherence-ring-container">
                <svg class="circular-progress" width="80" height="80" viewBox="0 0 80 80">
                  <circle class="progress-track" cx="40" cy="40" r="34" fill="none" stroke-width="6"/>
                  <circle class="progress-value" cx="40" cy="40" r="34" fill="none" stroke-width="6" 
                    stroke-dasharray="213.6" stroke-dashoffset="213.6" id="adherence-ring"/>
                </svg>
                <div class="adherence-ring-text">
                  <span class="text-2xl font-bold" id="adherence-percent">--</span>
                  <span class="text-xs text-secondary">%</span>
                </div>
              </div>
              <div class="adherence-stats">
                <div class="adherence-stat">
                  <span class="stat-dot bg-success"></span>
                  <span class="text-sm text-secondary">${i18n.t('taken')}</span>
                  <span class="font-semibold" id="stat-taken">-</span>
                </div>
                <div class="adherence-stat">
                  <span class="stat-dot bg-warning"></span>
                  <span class="text-sm text-secondary">${i18n.t('skipped')}</span>
                  <span class="font-semibold" id="stat-skipped">-</span>
                </div>
                <div class="adherence-stat">
                  <span class="stat-dot bg-error"></span>
                  <span class="text-sm text-secondary">${i18n.t('missed')}</span>
                  <span class="font-semibold" id="stat-missed">-</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Today's Medications -->
        <div class="section mt-6">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold">${i18n.t('today_meds')}</h3>
            <a href="#/medications" class="text-sm text-accent">${i18n.t('nav_meds')}</a>
          </div>
          <div id="today-meds-list" class="stagger-children">
            <!-- Skeleton loading -->
            <div class="skeleton skeleton-card mb-3"></div>
            <div class="skeleton skeleton-card mb-3"></div>
          </div>
        </div>

        <!-- Last Scan -->
        <div class="section mt-6 mb-6">
          <h3 class="font-semibold mb-3">${i18n.t('last_scan')}</h3>
          <div id="last-scan-card">
            <div class="skeleton skeleton-card"></div>
          </div>
        </div>
      </div>
    `;
  },

  async mount() {
    // Quick scan
    document.getElementById('quick-scan-card')?.addEventListener('click', () => {
      router.navigate('/scanner');
    });

    // Leaflet summary scan
    document.getElementById('leaflet-scan-card')?.addEventListener('click', () => {
      router.navigate('/leaflet-scanner');
    });

    // Search button
    document.getElementById('search-btn')?.addEventListener('click', () => {
      router.navigate('/drug-search');
    });

    // Load data
    this.loadAdherence();
    this.loadMedications();
    this.loadLastScan();
  },

  async loadAdherence() {
    try {
      const stats = await api.getAdherenceStats('week');
      const percent = Math.round(stats.adherence_rate || 0);
      const circumference = 2 * Math.PI * 34; // r=34
      const offset = circumference - (percent / 100) * circumference;

      const ring = document.getElementById('adherence-ring');
      const percentEl = document.getElementById('adherence-percent');
      if (ring) {
        ring.style.strokeDasharray = circumference;
        setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
      }
      if (percentEl) percentEl.textContent = percent;

      document.getElementById('stat-taken').textContent = stats.taken || 0;
      document.getElementById('stat-skipped').textContent = stats.skipped || 0;
      document.getElementById('stat-missed').textContent = stats.missed || 0;
    } catch {
      // Show defaults
      const percentEl = document.getElementById('adherence-percent');
      if (percentEl) percentEl.textContent = '0';
    }
  },

  async loadMedications() {
    const container = document.getElementById('today-meds-list');
    if (!container) return;

    try {
      const meds = await api.getMedications(true);

      if (!meds || meds.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-icon">💊</div>
            <p class="text-secondary">${i18n.t('no_meds_today')}</p>
            <button class="btn btn-primary btn-sm mt-3" id="add-first-med">${i18n.t('add_first_med')}</button>
          </div>
        `;
        document.getElementById('add-first-med')?.addEventListener('click', () => {
          router.navigate('/medications');
        });
        return;
      }

      container.innerHTML = meds.slice(0, 5).map(med => `
        <div class="med-card card card-interactive animate-fade-in-up" data-id="${med.id}">
          <div class="med-card-content">
            <div class="med-card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3"/>
              </svg>
            </div>
            <div class="med-card-info">
              <h4 class="font-semibold text-sm">${i18n.lang === 'ar' ? (med.drug_name_ar || med.custom_name || med.drug_name_en || '') : (med.drug_name_en || med.custom_name || '')}</h4>
              <p class="text-xs text-secondary">${med.dosage || ''} • ${this.getFrequencyLabel(med.frequency)}</p>
            </div>
            <div class="med-card-status">
              <span class="badge badge-warning">${i18n.t('pending')}</span>
            </div>
          </div>
        </div>
      `).join('');
    } catch {
      container.innerHTML = `
        <div class="empty-state">
          <p class="text-secondary text-sm">${i18n.t('error_generic')}</p>
          <button class="btn btn-ghost btn-sm mt-2" onclick="location.reload()">${i18n.t('retry')}</button>
        </div>
      `;
    }
  },

  async loadLastScan() {
    const container = document.getElementById('last-scan-card');
    if (!container) return;

    try {
      const history = await api.getScanHistory(1);
      if (!history || history.length === 0) {
        container.innerHTML = `
          <div class="card" style="text-align:center;padding:var(--space-6);">
            <p class="text-secondary text-sm">${i18n.t('no_data')}</p>
          </div>
        `;
        return;
      }

      const scan = history[0];
      const drugName = i18n.lang === 'ar' ? (scan.drug_name_ar || scan.drug_name_en || '-') : (scan.drug_name_en || '-');
      const confidence = Math.round((scan.confidence_score || 0) * 100);
      const date = new Date(scan.scanned_at).toLocaleDateString(i18n.lang === 'ar' ? 'ar-SA' : 'en-US');

      container.innerHTML = `
        <div class="card card-interactive animate-fade-in-up" id="last-scan-item">
          <div class="flex items-center gap-3">
            <div class="scan-thumb">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="3"/><line x1="3" y1="12" x2="21" y2="12"/></svg>
            </div>
            <div class="flex-1">
              <h4 class="font-semibold text-sm">${drugName}</h4>
              <p class="text-xs text-secondary">${date} • ${confidence}% ${i18n.t('confidence')}</p>
            </div>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}"/></svg>
          </div>
        </div>
      `;
    } catch {
      container.innerHTML = `<div class="card"><p class="text-secondary text-sm text-center">${i18n.t('no_data')}</p></div>`;
    }
  },

  getGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return i18n.t('greeting_morning');
    if (hour < 18) return i18n.t('greeting_afternoon');
    return i18n.t('greeting_evening');
  },

  getFrequencyLabel(freq) {
    const map = {
      daily: i18n.t('frequency_daily'),
      twice_daily: i18n.t('frequency_twice'),
      three_times_daily: i18n.t('frequency_three'),
      weekly: i18n.t('frequency_weekly'),
      custom: i18n.t('frequency_custom'),
    };
    return map[freq] || freq || '';
  },

  unmount() {}
};

export default HomePage;
