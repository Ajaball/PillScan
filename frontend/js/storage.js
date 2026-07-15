/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Storage Manager
   localStorage abstraction with namespacing and JSON support
   ═══════════════════════════════════════════════════════════════════ */

const PREFIX = 'pillscan_';

const storage = {
  /** Set a value (auto JSON-serializes objects) */
  set(key, value) {
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(PREFIX + key, serialized);
    } catch (e) {
      console.warn('Storage set error:', e);
    }
  },

  /** Get a value (auto JSON-parses) */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(PREFIX + key);
      if (item === null) return defaultValue;
      return JSON.parse(item);
    } catch (e) {
      return defaultValue;
    }
  },

  /** Remove a key */
  remove(key) {
    localStorage.removeItem(PREFIX + key);
  },

  /** Check if key exists */
  has(key) {
    return localStorage.getItem(PREFIX + key) !== null;
  },

  /** Clear all PillScan data */
  clear() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX));
    keys.forEach(k => localStorage.removeItem(k));
  },

  // ── Auth Token Shortcuts ────────────────────────────────────────

  /** Store authentication tokens */
  setTokens(accessToken, refreshToken) {
    this.set('access_token', accessToken);
    this.set('refresh_token', refreshToken);
  },

  /** Get access token */
  getAccessToken() {
    return this.get('access_token');
  },

  /** Get refresh token */
  getRefreshToken() {
    return this.get('refresh_token');
  },

  /** Clear auth tokens */
  clearTokens() {
    this.remove('access_token');
    this.remove('refresh_token');
    this.remove('user');
  },

  /** Check if user is authenticated */
  isAuthenticated() {
    return !!this.getAccessToken();
  },

  // ── User Data ───────────────────────────────────────────────────

  /** Store user profile */
  setUser(user) {
    this.set('user', user);
  },

  /** Get stored user profile */
  getUser() {
    return this.get('user');
  },

  /** Whether the stored user is an admin */
  isAdmin() {
    const user = this.getUser();
    return !!user && (user.role === 'ADMIN' || user.is_admin === true);
  },

  // ── App Settings ────────────────────────────────────────────────

  /** Check if onboarding was completed */
  isOnboardingDone() {
    return this.get('onboarding_done', false);
  },

  /** Mark onboarding as completed */
  setOnboardingDone() {
    this.set('onboarding_done', true);
  },

  /** Get theme preference */
  getTheme() {
    return this.get('theme', 'dark');
  },

  /** Set theme preference */
  setTheme(theme) {
    this.set('theme', theme);
  },

  /** Get font size scale */
  getFontScale() {
    return this.get('font_scale', 1);
  },

  /** Set font size scale */
  setFontScale(scale) {
    this.set('font_scale', scale);
  },

  /** Get notifications preference */
  getNotificationsEnabled() {
    return this.get('notifications', true);
  },

  /** Set notifications preference */
  setNotificationsEnabled(enabled) {
    this.set('notifications', enabled);
  },

  // ── Cache ───────────────────────────────────────────────────────

  /** Cache API response with TTL (in seconds) */
  cacheSet(key, data, ttlSeconds = 300) {
    this.set('cache_' + key, {
      data,
      expires: Date.now() + (ttlSeconds * 1000),
    });
  },

  /** Get cached data (returns null if expired) */
  cacheGet(key) {
    const cached = this.get('cache_' + key);
    if (!cached) return null;
    if (Date.now() > cached.expires) {
      this.remove('cache_' + key);
      return null;
    }
    return cached.data;
  },

  /** Clear all cache entries */
  cacheClear() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(PREFIX + 'cache_'));
    keys.forEach(k => localStorage.removeItem(k));
  },
};

export default storage;
