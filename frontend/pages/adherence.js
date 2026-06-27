/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Adherence Tracking Page
   Stats circle, calendar heatmap, and streak display
   ═══════════════════════════════════════════════════════════════════ */
import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';

const AdherencePage = {
  currentPeriod: 'week',
  render() {
    return `
      <div class="page-header">
        <h1 class="page-title">${i18n.t('adherence')}</h1>
        <button class="btn btn-icon btn-secondary" id="scan-history-btn" aria-label="${i18n.t('scan_history')}">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="12" x2="21" y2="12"/></svg>
        </button>
      </div>
      <div class="page-content">
        <!-- Period Selector -->
        <div class="period-tabs">
          <button class="period-tab active" data-period="week">${i18n.t('period_week')}</button>
          <button class="period-tab" data-period="month">${i18n.t('period_month')}</button>
          <button class="period-tab" data-period="year">${i18n.t('period_year')}</button>
        </div>

        <!-- Stats Card -->
        <div class="card card-glow mt-4" id="stats-card">
          <div class="adherence-main">
            <div class="adherence-circle-container">
              <svg class="circular-progress" width="140" height="140" viewBox="0 0 140 140">
                <circle class="progress-track" cx="70" cy="70" r="58" fill="none" stroke-width="10"/>
                <circle class="progress-value" cx="70" cy="70" r="58" fill="none" stroke-width="10"
                  stroke-dasharray="364.4" stroke-dashoffset="364.4" id="main-ring"
                  style="transition: stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1);"/>
              </svg>
              <div class="adherence-circle-text">
                <span class="text-3xl font-extrabold" id="main-percent">--</span>
                <span class="text-sm text-secondary">%</span>
              </div>
            </div>
            <div id="adherence-message" class="text-center mt-2 font-medium"></div>
          </div>

          <!-- Streak -->
          <div class="streak-card mt-4">
            <span class="streak-fire">🔥</span>
            <div>
              <p class="font-bold text-lg" id="streak-count">-</p>
              <p class="text-xs text-secondary">${i18n.t('streak')}</p>
            </div>
          </div>

          <!-- Stats Grid -->
          <div class="grid grid-3 gap-3 mt-4">
            <div class="stat-box stat-success">
              <p class="stat-number" id="s-taken">-</p>
              <p class="stat-label">${i18n.t('taken')}</p>
            </div>
            <div class="stat-box stat-warning">
              <p class="stat-number" id="s-skipped">-</p>
              <p class="stat-label">${i18n.t('skipped')}</p>
            </div>
            <div class="stat-box stat-error">
              <p class="stat-number" id="s-missed">-</p>
              <p class="stat-label">${i18n.t('missed')}</p>
            </div>
          </div>
        </div>

        <!-- Calendar -->
        <div class="card mt-4">
          <h3 class="font-semibold mb-3">${i18n.t('calendar_view')}</h3>
          <div class="calendar-header flex items-center justify-between mb-2">
            <button class="btn btn-icon-sm btn-ghost" id="cal-prev">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
            </button>
            <span class="font-medium" id="cal-month-label"></span>
            <button class="btn btn-icon-sm btn-ghost" id="cal-next">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}"/></svg>
            </button>
          </div>
          <div class="calendar-grid" id="calendar-grid"></div>
        </div>
      </div>
    `;
  },

  async mount() {
    document.getElementById('scan-history-btn')?.addEventListener('click', () => router.navigate('/drug-search'));

    // Period tabs
    document.querySelectorAll('.period-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.period-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentPeriod = tab.dataset.period;
        this.loadStats();
      });
    });

    // Calendar navigation
    this.calendarDate = new Date();
    document.getElementById('cal-prev')?.addEventListener('click', () => { this.calendarDate.setMonth(this.calendarDate.getMonth() - 1); this.loadCalendar(); });
    document.getElementById('cal-next')?.addEventListener('click', () => { this.calendarDate.setMonth(this.calendarDate.getMonth() + 1); this.loadCalendar(); });

    await Promise.all([this.loadStats(), this.loadCalendar()]);
  },

  async loadStats() {
    try {
      const stats = await api.getAdherenceStats(this.currentPeriod);
      const percent = Math.round(stats.adherence_rate || 0);
      const circumference = 2 * Math.PI * 58;
      const offset = circumference - (percent / 100) * circumference;

      const ring = document.getElementById('main-ring');
      if (ring) {
        ring.style.strokeDasharray = circumference;
        ring.style.stroke = percent >= 80 ? 'var(--color-success)' : percent >= 50 ? 'var(--color-warning)' : 'var(--color-error)';
        setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
      }

      const percentEl = document.getElementById('main-percent');
      if (percentEl) this.animateCount(percentEl, percent);

      document.getElementById('s-taken').textContent = stats.taken || 0;
      document.getElementById('s-skipped').textContent = stats.skipped || 0;
      document.getElementById('s-missed').textContent = stats.missed || 0;
      document.getElementById('streak-count').textContent = stats.streak_days || 0;

      const msgEl = document.getElementById('adherence-message');
      if (msgEl) {
        if (percent >= 90) msgEl.innerHTML = `<span class="text-success">${i18n.t('great_job')}</span>`;
        else if (percent >= 60) msgEl.innerHTML = `<span class="text-warning">${i18n.t('keep_going')}</span>`;
        else msgEl.innerHTML = `<span class="text-error">${i18n.t('needs_improvement')}</span>`;
      }
    } catch { /* defaults shown */ }
  },

  async loadCalendar() {
    const grid = document.getElementById('calendar-grid');
    const label = document.getElementById('cal-month-label');
    if (!grid || !label) return;

    const year = this.calendarDate.getFullYear();
    const month = this.calendarDate.getMonth();
    const monthStr = `${year}-${String(month + 1).padStart(2, '0')}`;
    label.textContent = new Date(year, month).toLocaleDateString(i18n.lang === 'ar' ? 'ar-SA' : 'en-US', { year: 'numeric', month: 'long' });

    // Day headers
    const dayNames = [i18n.t('day_sat'), i18n.t('day_sun'), i18n.t('day_mon'), i18n.t('day_tue'), i18n.t('day_wed'), i18n.t('day_thu'), i18n.t('day_fri')];
    let html = dayNames.map(d => `<div class="cal-day-name">${d}</div>`).join('');

    // Load data
    let calData = {};
    try {
      const data = await api.getAdherenceCalendar(monthStr);
      if (data?.days) data.days.forEach(d => { calData[d.date] = d; });
    } catch { /* empty calendar */ }

    const firstDay = new Date(year, month, 1);
    let startDay = firstDay.getDay(); // 0=Sun
    startDay = startDay === 0 ? 1 : startDay === 6 ? 0 : startDay + 1; // Adjust for Sat-first

    for (let i = 0; i < startDay; i++) html += `<div class="cal-cell empty"></div>`;

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      const dayData = calData[dateStr];
      const isToday = today.getFullYear() === year && today.getMonth() === month && today.getDate() === d;

      let cls = 'cal-cell';
      if (isToday) cls += ' today';
      if (dayData) {
        if (dayData.taken === dayData.total) cls += ' full';
        else if (dayData.taken > 0) cls += ' partial';
        else cls += ' none';
      }

      html += `<div class="${cls}">${d}</div>`;
    }

    grid.innerHTML = html;
  },

  animateCount(el, target) {
    let current = 0;
    const step = Math.max(1, Math.floor(target / 30));
    const interval = setInterval(() => {
      current += step;
      if (current >= target) { current = target; clearInterval(interval); }
      el.textContent = current;
    }, 30);
  },

  unmount() {}
};

export default AdherencePage;
