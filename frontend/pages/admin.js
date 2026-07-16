/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Admin Panel
   Approve/reject sign-up requests and manage all users. Admin only —
   the server also enforces the ADMIN role on every endpoint used here.
   ═══════════════════════════════════════════════════════════════════ */

import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import toast from '../components/toast.js';

const STATUS_BADGE = {
  PENDING: 'badge-warning',
  APPROVED: 'badge-success',
  REJECTED: 'badge-error',
};

// Bump this when the admin panel changes so deploys are easy to verify at a glance.
const PANEL_VERSION = 'v6';

const AdminPage = {
  render() {
    return `
      <div class="page-header">
        <button class="btn btn-icon btn-secondary" id="back-btn">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'}"/></svg>
        </button>
        <h1 class="page-title">${i18n.t('admin_panel')}</h1>
        <div style="width:48px;"></div>
      </div>
      <div class="page-content">
        <!-- Storage status -->
        <div id="db-status" class="mb-4"></div>

        <!-- Overview stats -->
        <div class="section">
          <h3 class="font-semibold mb-3">${i18n.t('admin_stats_title')}</h3>
          <div id="admin-stats" class="grid grid-2 gap-3">
            <div class="skeleton skeleton-card"></div>
            <div class="skeleton skeleton-card"></div>
          </div>
        </div>

        <!-- Pending requests -->
        <div class="section">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-semibold">${i18n.t('admin_pending_requests')}</h3>
            <span class="badge badge-warning text-xs" id="pending-count">0</span>
          </div>
          <div id="pending-list" class="stagger-children">
            <div class="skeleton skeleton-card mb-3"></div>
          </div>
        </div>

        <!-- All users -->
        <div class="section mt-6 mb-6">
          <h3 class="font-semibold mb-3">${i18n.t('admin_all_users')}</h3>
          <div id="users-list" class="stagger-children">
            <div class="skeleton skeleton-card mb-3"></div>
          </div>
        </div>

        <p class="text-center text-xs text-tertiary mb-6">
          ${i18n.t('admin_version')}: <span dir="ltr">${PANEL_VERSION}</span>
        </p>
      </div>
    `;
  },

  async mount() {
    document.getElementById('back-btn')?.addEventListener('click', () => router.navigate('/profile'));
    await this.reload();
  },

  async reload() {
    await Promise.all([this.loadDbStatus(), this.loadPending(), this.loadAllUsers()]);
  },

  async loadDbStatus() {
    const container = document.getElementById('db-status');
    if (!container) return;
    try {
      const s = await api.getDbStatus();
      const ok = s.persistent === true;
      const color = ok ? 'var(--color-success)' : 'var(--color-warning)';
      const msg = ok ? i18n.t('db_persistent') : i18n.t('db_ephemeral');
      const host = s.host ? ` <span dir="ltr" class="text-tertiary">(${s.host})</span>` : '';
      container.innerHTML = `
        <div class="card" style="border-inline-start:4px solid ${color};">
          <p class="text-xs font-semibold mb-1">${i18n.t('db_status_title')}</p>
          <p class="text-xs text-secondary" style="line-height:1.6;">${msg}${host}</p>
        </div>`;
    } catch {
      container.innerHTML = '';
    }
  },

  fmtDate(iso) {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleDateString(i18n.lang === 'ar' ? 'ar-SA' : 'en-US');
    } catch { return ''; }
  },

  async loadPending() {
    const container = document.getElementById('pending-list');
    const countEl = document.getElementById('pending-count');
    if (!container) return;

    try {
      const users = await api.getUsers('PENDING');
      if (countEl) countEl.textContent = users.length;

      if (!users.length) {
        container.innerHTML = `<div class="empty-state"><div class="text-4xl mb-2">✅</div><p class="text-secondary text-sm">${i18n.t('admin_no_pending')}</p></div>`;
        return;
      }

      container.innerHTML = users.map(u => `
        <div class="card animate-fade-in-up mb-3" data-id="${u.id}">
          <div class="flex items-center gap-3 mb-3">
            <div class="avatar avatar-md" style="background:var(--color-primary-gradient);">${(u.full_name || 'U').charAt(0)}</div>
            <div class="flex-1">
              <h4 class="font-semibold text-sm">${u.full_name || '-'}</h4>
              <p class="text-xs text-tertiary" dir="ltr">${u.email || ''}</p>
              <p class="text-xs text-tertiary" dir="ltr">${u.phone || ''}</p>
              <p class="text-xs text-secondary mt-1">${i18n.t('admin_request_date')}: ${this.fmtDate(u.created_at)}</p>
            </div>
          </div>
          <div class="flex gap-2">
            <button class="btn btn-primary btn-sm flex-1 act-approve" data-id="${u.id}">${i18n.t('admin_approve')}</button>
            <button class="btn btn-ghost btn-sm flex-1 act-reject" data-id="${u.id}" style="color:var(--color-error);">${i18n.t('admin_reject')}</button>
          </div>
        </div>
      `).join('');

      container.querySelectorAll('.act-approve').forEach(btn =>
        btn.addEventListener('click', () => this.changeStatus(btn.dataset.id, 'APPROVED')));
      container.querySelectorAll('.act-reject').forEach(btn =>
        btn.addEventListener('click', () => this.changeStatus(btn.dataset.id, 'REJECTED')));
    } catch (err) {
      container.innerHTML = `<p class="text-center text-secondary text-sm">${err.message || i18n.t('error_generic')}</p>`;
    }
  },

  async loadAllUsers() {
    const container = document.getElementById('users-list');
    if (!container) return;

    try {
      const users = await api.getUsers();
      this.renderStats(users);
      if (!users.length) {
        container.innerHTML = `<p class="text-center text-secondary text-sm">${i18n.t('admin_no_users')}</p>`;
        return;
      }

      container.innerHTML = users.map(u => {
        const statusKey = `status_${(u.status || '').toLowerCase()}`;
        const roleKey = u.role === 'ADMIN' ? 'role_admin' : 'role_user';
        return `
        <div class="card animate-fade-in-up mb-3" data-id="${u.id}">
          <div class="flex items-center gap-3">
            <div class="flex-1">
              <h4 class="font-semibold text-sm">${u.full_name || '-'} <span class="text-xs text-tertiary">(${i18n.t(roleKey)})</span></h4>
              <p class="text-xs text-tertiary" dir="ltr">${u.email || ''}</p>
            </div>
            <span class="badge ${STATUS_BADGE[u.status] || 'badge-primary'} text-xs">${i18n.t(statusKey)}</span>
          </div>
          <div class="flex gap-2 mt-3">
            <select class="input-field status-select" data-id="${u.id}" style="padding:8px 12px;font-size:13px;">
              <option value="PENDING" ${u.status === 'PENDING' ? 'selected' : ''}>${i18n.t('status_pending')}</option>
              <option value="APPROVED" ${u.status === 'APPROVED' ? 'selected' : ''}>${i18n.t('status_approved')}</option>
              <option value="REJECTED" ${u.status === 'REJECTED' ? 'selected' : ''}>${i18n.t('status_rejected')}</option>
            </select>
          </div>
        </div>`;
      }).join('');

      container.querySelectorAll('.status-select').forEach(sel =>
        sel.addEventListener('change', () => this.changeStatus(sel.dataset.id, sel.value)));
    } catch (err) {
      this.renderStats([]);
      container.innerHTML = `<p class="text-center text-secondary text-sm">${err.message || i18n.t('error_generic')}</p>`;
    }
  },

  renderStats(users) {
    const el = document.getElementById('admin-stats');
    if (!el) return;
    const by = (s) => users.filter(u => u.status === s).length;
    const cards = [
      { label: 'admin_stat_total', value: users.length, cls: 'stat-total' },
      { label: 'admin_stat_pending', value: by('PENDING'), cls: 'stat-warning' },
      { label: 'admin_stat_approved', value: by('APPROVED'), cls: 'stat-success' },
      { label: 'admin_stat_rejected', value: by('REJECTED'), cls: 'stat-error' },
    ];
    el.className = 'grid grid-2 gap-3';
    el.innerHTML = cards.map(c => `
      <div class="stat-box ${c.cls}">
        <div class="stat-number">${c.value}</div>
        <div class="stat-label">${i18n.t(c.label)}</div>
      </div>`).join('');
  },

  async changeStatus(userId, status) {
    try {
      await api.updateUserStatus(userId, status);
      toast.success(i18n.t('admin_status_updated'));
      // Instant UI refresh
      await this.reload();
    } catch (err) {
      toast.error(err.message || i18n.t('error_generic'));
      await this.reload();
    }
  },

  unmount() {},
};

export default AdminPage;
