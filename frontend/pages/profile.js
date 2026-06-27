/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Profile & Settings Page
   ═══════════════════════════════════════════════════════════════════ */
import i18n from '../js/i18n.js';
import router from '../js/router.js';
import api from '../js/api.js';
import storage from '../js/storage.js';
import toast from '../components/toast.js';

const ProfilePage = {
  render() {
    const user = storage.getUser() || {};
    const initials = (user.full_name || 'U').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
    const theme = storage.getTheme();

    return `
      <div class="page-header">
        <h1 class="page-title">${i18n.t('profile')}</h1>
        <div style="width:48px;"></div>
      </div>
      <div class="page-content">
        <!-- Profile Card -->
        <div class="card card-glow animate-fade-in-up profile-card">
          <div class="flex items-center gap-4">
            <div class="avatar avatar-xl">${initials}</div>
            <div class="flex-1">
              <h2 class="text-lg font-bold">${user.full_name || '-'}</h2>
              <p class="text-sm text-secondary" dir="ltr">${user.email || '-'}</p>
              ${user.phone ? `<p class="text-xs text-tertiary mt-1" dir="ltr">${user.phone}</p>` : ''}
            </div>
          </div>
        </div>

        <!-- Settings -->
        <h3 class="font-semibold mt-6 mb-3">${i18n.t('settings')}</h3>

        <div class="settings-list stagger-children">
          <!-- Language -->
          <div class="card card-interactive animate-fade-in-up settings-item" id="lang-setting">
            <div class="flex items-center gap-3">
              <div class="settings-icon">🌐</div>
              <div class="flex-1">
                <p class="font-medium">${i18n.t('language')}</p>
                <p class="text-xs text-secondary">${i18n.lang === 'ar' ? i18n.t('arabic') : i18n.t('english')}</p>
              </div>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}"/></svg>
            </div>
          </div>

          <!-- Dark Mode -->
          <div class="card animate-fade-in-up settings-item mt-2">
            <div class="flex items-center gap-3">
              <div class="settings-icon">🌙</div>
              <div class="flex-1">
                <p class="font-medium">${i18n.t('dark_mode')}</p>
              </div>
              <label class="toggle">
                <input type="checkbox" id="dark-mode-toggle" ${theme === 'dark' ? 'checked' : ''}>
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>

          <!-- Notifications -->
          <div class="card animate-fade-in-up settings-item mt-2">
            <div class="flex items-center gap-3">
              <div class="settings-icon">🔔</div>
              <div class="flex-1">
                <p class="font-medium">${i18n.t('notifications')}</p>
              </div>
              <label class="toggle">
                <input type="checkbox" id="notif-toggle" ${storage.getNotificationsEnabled() ? 'checked' : ''}>
                <span class="toggle-track"></span>
              </label>
            </div>
          </div>

          <!-- Reminders -->
          <div class="card card-interactive animate-fade-in-up settings-item mt-2" id="reminders-setting">
            <div class="flex items-center gap-3">
              <div class="settings-icon">⏰</div>
              <div class="flex-1">
                <p class="font-medium">${i18n.t('reminders')}</p>
              </div>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-tertiary)" stroke-width="2" stroke-linecap="round"><path d="${i18n.isRTL ? 'M15 18l-6-6 6-6' : 'M9 18l6-6-6-6'}"/></svg>
            </div>
          </div>

          <!-- About -->
          <div class="card animate-fade-in-up settings-item mt-2">
            <div class="flex items-center gap-3">
              <div class="settings-icon">ℹ️</div>
              <div class="flex-1">
                <p class="font-medium">${i18n.t('about')}</p>
                <p class="text-xs text-tertiary">${i18n.t('version')} 1.0.0</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Danger Zone -->
        <div class="mt-8 mb-4">
          <button class="btn btn-ghost btn-block" id="logout-btn" style="color:var(--color-warning);">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
            ${i18n.t('logout')}
          </button>
          <button class="btn btn-ghost btn-block mt-2" id="delete-account-btn" style="color:var(--color-error);">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
            ${i18n.t('delete_account')}
          </button>
        </div>

        <p class="text-center text-xs text-tertiary mb-6">
          PillScan © 2026 — جامعة تبوك
        </p>
      </div>
    `;
  },

  mount() {
    // Language toggle
    document.getElementById('lang-setting')?.addEventListener('click', () => {
      i18n.toggleLang();
      router.navigate('/profile');
    });

    // Dark mode toggle
    document.getElementById('dark-mode-toggle')?.addEventListener('change', (e) => {
      const theme = e.target.checked ? 'dark' : 'light';
      storage.setTheme(theme);
      document.documentElement.setAttribute('data-theme', theme);
    });

    // Notifications toggle
    document.getElementById('notif-toggle')?.addEventListener('change', (e) => {
      storage.setNotificationsEnabled(e.target.checked);
    });

    // Reminders
    document.getElementById('reminders-setting')?.addEventListener('click', () => {
      router.navigate('/reminders');
    });

    // Logout
    document.getElementById('logout-btn')?.addEventListener('click', () => {
      if (confirm(i18n.t('logout_confirm'))) {
        storage.clearTokens();
        storage.cacheClear();
        router.navigate('/login');
        toast.info(i18n.t('logout'));
      }
    });

    // Delete account
    document.getElementById('delete-account-btn')?.addEventListener('click', async () => {
      if (confirm(i18n.t('delete_account_confirm'))) {
        try {
          await api.deleteAccount();
          storage.clear();
          router.navigate('/login');
          toast.info(i18n.t('success'));
        } catch (err) {
          toast.error(err.message);
        }
      }
    });
  },

  unmount() {}
};

export default ProfilePage;
