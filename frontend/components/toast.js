/* ═══════════════════════════════════════════════════════════════════
   PillScan PWA — Toast Notification Component
   ═══════════════════════════════════════════════════════════════════ */

class Toast {
  constructor() {
    this.container = null;
    this.timeout = null;
  }

  init() {
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.style.cssText = `
        position: fixed;
        top: calc(env(safe-area-inset-top, 0px) + 12px);
        left: 50%;
        transform: translateX(-50%);
        z-index: 200;
        width: calc(100% - 32px);
        max-width: 440px;
        pointer-events: none;
      `;
      document.body.appendChild(this.container);
    }
  }

  show(message, type = 'info', duration = 3000) {
    this.init();

    // Clear existing
    if (this.timeout) clearTimeout(this.timeout);
    this.container.innerHTML = '';

    const icons = {
      success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M20 6L9 17l-5-5"/></svg>`,
      error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
      warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
      info: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
    };

    const colors = {
      success: { bg: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)', text: '#34D399' },
      error: { bg: 'rgba(239, 68, 68, 0.15)', border: 'rgba(239, 68, 68, 0.3)', text: '#F87171' },
      warning: { bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.3)', text: '#FBBF24' },
      info: { bg: 'rgba(37, 99, 235, 0.15)', border: 'rgba(37, 99, 235, 0.3)', text: '#60A5FA' },
    };

    const c = colors[type] || colors.info;

    const toast = document.createElement('div');
    toast.style.cssText = `
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 18px;
      background: ${c.bg};
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid ${c.border};
      border-radius: 14px;
      color: var(--color-text-primary, #F1F5F9);
      font-size: 14px;
      font-weight: 500;
      pointer-events: auto;
      animation: toastSlideIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    `;

    toast.innerHTML = `
      <span style="color: ${c.text}; flex-shrink: 0;">${icons[type] || icons.info}</span>
      <span style="flex: 1;">${message}</span>
    `;

    this.container.appendChild(toast);

    // Auto dismiss
    this.timeout = setTimeout(() => {
      toast.style.animation = 'toastSlideOut 0.3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    }, duration);

    // Click to dismiss
    toast.addEventListener('click', () => {
      clearTimeout(this.timeout);
      toast.style.animation = 'toastSlideOut 0.3s ease-out forwards';
      setTimeout(() => toast.remove(), 300);
    });
  }

  success(message, duration) { this.show(message, 'success', duration); }
  error(message, duration)   { this.show(message, 'error', duration); }
  warning(message, duration) { this.show(message, 'warning', duration); }
  info(message, duration)    { this.show(message, 'info', duration); }
}

const toast = new Toast();
export default toast;
