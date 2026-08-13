/**
 * QuizNova — Main Application JS v2
 * Premium animations, interactions, and utilities
 * ================================================
 */

'use strict';

// ─── PAGE LOADER ─────────────────────────────────────────────────────────────
;(function () {
  const loader = document.getElementById('page-loader');
  if (!loader) return;

  const hide = () => {
    if (loader._hidden) return;
    loader._hidden = true;
    loader.style.transition = 'opacity 0.4s ease';
    loader.style.opacity = '0';
    setTimeout(() => {
      loader.style.display = 'none';
      document.body.classList.add('page-ready');
      if (typeof _initEntrance === 'function') {
        try { _initEntrance(); } catch (e) { console.warn('Entrance animation notice:', e); }
      }
    }, 400);
  };

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(hide, 80);
  } else {
    window.addEventListener('DOMContentLoaded', () => setTimeout(hide, 80));
    window.addEventListener('load', () => setTimeout(hide, 80));
  }
  // Fail-safe guarantee
  setTimeout(hide, 1000);
})();

// ─── PAGE ENTRANCE ANIMATIONS ────────────────────────────────────────────────
function _initEntrance() {
  if (typeof AOS !== 'undefined') {
    AOS.init({
      duration: 700,
      once: true,
      offset: 40,
      easing: 'ease-out-cubic',
    });
  }

  if (typeof gsap === 'undefined') return;

  gsap.registerPlugin(ScrollTrigger);

  // Navbar slide in
  gsap.from('.navbar', {
    y: -80, opacity: 0, duration: 0.7, ease: 'power3.out', delay: 0.05,
  });

  // Hero elements stagger
  const heroTitle = document.querySelector('.hero-title');
  const heroSub   = document.querySelector('.hero-subtitle');
  const heroCta   = document.querySelector('.hero-cta');
  const heroTrust = document.querySelector('.hero-trust');
  const heroStats = document.querySelector('.hero-stats');

  if (heroTitle) {
    gsap.timeline({ delay: 0.2 })
      .from(heroTitle,    { opacity: 0, y: 60, duration: 0.9, ease: 'power4.out' })
      .from(heroSub,      { opacity: 0, y: 30, duration: 0.7, ease: 'power3.out' }, '-=0.5')
      .from(heroCta,      { opacity: 0, y: 20, scale: 0.95, duration: 0.6, ease: 'back.out(1.7)' }, '-=0.4')
      .from(heroTrust,    { opacity: 0, duration: 0.5 }, '-=0.3')
      .from(heroStats,    { opacity: 0, y: 20, duration: 0.6 }, '-=0.2');
  }

  // Sphere entrance
  const sphere = document.querySelector('.hero-sphere');
  if (sphere) {
    gsap.from(sphere, {
      opacity: 0, scale: 0.6, rotation: 20,
      duration: 1.2, ease: 'power3.out', delay: 0.4,
    });
  }

  // ScrollTrigger for stat cards
  gsap.utils.toArray('.stat-card').forEach((el, i) => {
    gsap.from(el, {
      scrollTrigger: { trigger: el, start: 'top 88%' },
      opacity: 0, y: 40, duration: 0.6, ease: 'power2.out',
      delay: i * 0.08,
    });
  });

  // Feature cards stagger
  gsap.utils.toArray('.feature-card').forEach((el, i) => {
    gsap.from(el, {
      scrollTrigger: { trigger: el, start: 'top 88%' },
      opacity: 0, y: 40, duration: 0.6, ease: 'power2.out',
      delay: i * 0.07,
    });
  });
}

// ─── PARTICLE CANVAS ─────────────────────────────────────────────────────────
;(function () {
  const canvas = document.getElementById('particles-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let W = canvas.width  = window.innerWidth;
  let H = canvas.height = window.innerHeight;
  let mouse = { x: W / 2, y: H / 2 };

  const PARTICLE_COUNT = 70;
  const particles = Array.from({ length: PARTICLE_COUNT }, () => ({
    x:  Math.random() * W,
    y:  Math.random() * H,
    vx: (Math.random() - 0.5) * 0.35,
    vy: (Math.random() - 0.5) * 0.35,
    r:  Math.random() * 1.8 + 0.4,
    a:  Math.random() * 0.5 + 0.08,
    hue: Math.random() > 0.55 ? '124,58,237' : '37,99,235',
  }));

  canvas.addEventListener('mousemove', e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  function draw() {
    ctx.clearRect(0, 0, W, H);
    particles.forEach(p => {
      // Mouse attraction
      const dx = mouse.x - p.x;
      const dy = mouse.y - p.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 200) {
        p.vx += (dx / dist) * 0.015;
        p.vy += (dy / dist) * 0.015;
      }

      p.vx *= 0.99;
      p.vy *= 0.99;
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.hue},${p.a})`;
      ctx.fill();
    });

    // Connecting lines
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d  = Math.sqrt(dx * dx + dy * dy);
        if (d < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(124,58,237,${0.06 * (1 - d / 120)})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    requestAnimationFrame(draw);
  }

  draw();

  window.addEventListener('resize', () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  });
})();

// ─── FLASH MESSAGES ──────────────────────────────────────────────────────────
function dismissFlash(el) {
  if (!el || el._gone) return;
  el._gone = true;
  el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
  el.style.opacity    = '0';
  el.style.transform  = 'translateX(110%)';
  setTimeout(() => el.remove(), 320);
}

function showFlash(message, type = 'info') {
  let container = document.querySelector('.flash-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'flash-container';
    document.body.appendChild(container);
  }

  const icons = {
    success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`,
    error:   `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`,
    warning: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    info:    `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  };

  const el = document.createElement('div');
  el.className = `flash ${type}`;
  el.innerHTML = `
    ${icons[type] || icons.info}
    <span class="flash-text">${message}</span>
    <button class="flash-close" onclick="dismissFlash(this.parentElement)" aria-label="Dismiss">
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>`;

  container.appendChild(el);

  if (typeof gsap !== 'undefined') {
    gsap.from(el, { x: 120, opacity: 0, duration: 0.35, ease: 'power2.out' });
  }

  setTimeout(() => dismissFlash(el), 5500);
}

;(function initExistingFlash() {
  document.querySelectorAll('.flash').forEach((el, i) => {
    setTimeout(() => dismissFlash(el), 5000 + i * 300);
    el.querySelector('.flash-close')?.addEventListener('click', () => dismissFlash(el));
  });
})();

// ─── MOBILE NAVIGATION ───────────────────────────────────────────────────────
;(function () {
  const hamburger = document.querySelector('.hamburger');
  const navLinks  = document.querySelector('.nav-links');
  const navActions = document.querySelector('.nav-actions');
  if (!hamburger) return;

  let open = false;
  const mobileMenu = document.createElement('div');
  mobileMenu.id = 'mobile-menu';
  mobileMenu.style.cssText = `
    position: fixed; inset: 0; top: var(--nav-h, 64px);
    background: rgba(8, 8, 16, 0.98); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
    z-index: 999; padding: 16px 14px 32px 14px;
    flex-direction: column; gap: 8px; overflow-y: auto; overflow-x: hidden;
    display: none; border-top: 1px solid rgba(255,255,255,0.08); box-sizing: border-box;
  `;
  document.body.appendChild(mobileMenu);

  hamburger.addEventListener('click', () => {
    open = !open;
    hamburger.classList.toggle('is-open', open);

    if (open) {
      mobileMenu.innerHTML = '';
      
      // 1. Full-width compact mobile search input
      const searchWrap = document.createElement('div');
      searchWrap.style.cssText = 'position:relative; width:100%; margin-bottom:6px; box-sizing:border-box;';
      searchWrap.innerHTML = `
        <input type="text" placeholder="Search quizzes..." id="mobile-search-input"
               style="width:100%; height:44px; background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.12); border-radius:12px; padding:0 16px 0 40px; font-size:13.5px; color:#FFFFFF; outline:none; box-sizing:border-box; transition:border-color 0.2s ease;">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9898B0" stroke-width="2" style="position:absolute; left:14px; top:14px; pointer-events:none;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      `;
      mobileMenu.appendChild(searchWrap);

      // Add enter key listener to mobile search
      setTimeout(() => {
        const mobileSearchEl = document.getElementById('mobile-search-input');
        if (mobileSearchEl) {
          mobileSearchEl.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && mobileSearchEl.value.trim()) {
              window.location.href = '/categories?q=' + encodeURIComponent(mobileSearchEl.value.trim());
            }
          });
        }
      }, 50);

      // 2. Clone nav links as compact high-contrast list items (48px height)
      navLinks?.querySelectorAll('.nav-link').forEach(link => {
        const clone = link.cloneNode(true);
        clone.className = 'mobile-nav-link ' + (link.classList.contains('active') ? 'active' : '');
        clone.style.cssText = `
          display: flex; align-items: center; width: 100%; height: 48px;
          padding: 0 16px; font-size: 14.5px; font-weight: 600; font-family: var(--font-display);
          border-radius: 12px; color: #FFFFFF !important; text-decoration: none;
          background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08);
          box-sizing: border-box; transition: all 0.2s ease;
        `;
        if (link.classList.contains('active')) {
          clone.style.background = 'rgba(124, 58, 237, 0.2)';
          clone.style.borderColor = 'rgba(124, 58, 237, 0.5)';
        }
        mobileMenu.appendChild(clone);
      });

      // 3. Actions (Log In, Sign Up, Log Out, Dashboard)
      const actionsGroup = document.createElement('div');
      actionsGroup.style.cssText = 'display:flex; flex-direction:column; gap:8px; margin-top:6px; width:100%; box-sizing:border-box;';
      
      navActions?.querySelectorAll('a:not(.nav-avatar), button').forEach(el => {
        if (el.id === 'hamburger-btn') return;
        const clone = el.cloneNode(true);
        const isPrimary = clone.classList.contains('btn-primary');
        clone.style.cssText = `
          display: flex; align-items: center; justify-content: center; width: 100%; height: 46px;
          padding: 0 16px; font-size: 14px; font-weight: 700; border-radius: 12px; text-decoration: none;
          box-sizing: border-box; transition: all 0.2s ease;
          ${isPrimary 
            ? 'background: linear-gradient(135deg, #7C3AED, #2563EB); color: #FFFFFF !important; border: none; box-shadow: 0 0 15px rgba(124,58,237,0.3);' 
            : 'background: rgba(255, 255, 255, 0.06); color: #FFFFFF !important; border: 1px solid rgba(255, 255, 255, 0.12);'}
        `;
        actionsGroup.appendChild(clone);
      });
      
      if (actionsGroup.children.length > 0) {
        mobileMenu.appendChild(actionsGroup);
      }

      mobileMenu.style.display = 'flex';
      document.body.style.overflow = 'hidden';
      if (typeof gsap !== 'undefined') {
        gsap.from(mobileMenu.children, { opacity: 0, y: -8, stagger: 0.03, duration: 0.22, ease: 'power2.out' });
      }
    } else {
      mobileMenu.style.display = 'none';
      document.body.style.overflow = '';
    }
  });

  document.addEventListener('click', e => {
    if (open && !hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
      open = false;
      hamburger.classList.remove('is-open');
      mobileMenu.style.display = 'none';
      document.body.style.overflow = '';
    }
  });
})();

// ─── DASHBOARD SIDEBAR MOBILE ────────────────────────────────────────────────
;(function () {
  const toggle  = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('main-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (!toggle || !sidebar) return;

  const open  = () => { sidebar.classList.add('open');  overlay?.classList.add('active'); };
  const close = () => { sidebar.classList.remove('open'); overlay?.classList.remove('active'); };

  toggle.addEventListener('click', () => sidebar.classList.contains('open') ? close() : open());
  overlay?.addEventListener('click', close);
})();

// ─── NUMBER COUNTER ANIMATION ────────────────────────────────────────────────
function animateCount(el, target, duration = 1600) {
  const start = 0;
  const range  = target - start;
  const startTime = performance.now();
  const suffix = el.dataset.countSuffix || '';

  function step(now) {
    const elapsed  = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + range * eased).toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

;(function initCounters() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target._counted) {
        entry.target._counted = true;
        const target = parseInt(entry.target.dataset.countTarget || '0');
        animateCount(entry.target, target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('[data-count-target]').forEach(el => observer.observe(el));
})();

// ─── SMOOTH SCROLL ────────────────────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', e => {
    const href = link.getAttribute('href');
    if (href === '#') return;
    const target = document.querySelector(href);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ─── COPY TO CLIPBOARD ────────────────────────────────────────────────────────
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = 'Copied!';
      btn.style.color = 'var(--success)';
      setTimeout(() => { btn.textContent = orig; btn.style.color = ''; }, 2000);
    } else {
      showFlash('Copied to clipboard!', 'success');
    }
  }).catch(() => showFlash('Copy failed', 'error'));
}

// ─── CHART.JS GLOBAL DEFAULTS ─────────────────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.color           = '#9898B0';
  Chart.defaults.borderColor     = 'rgba(255,255,255,0.06)';
  Chart.defaults.font.family     = 'Inter, sans-serif';
  Chart.defaults.plugins.tooltip = {
    backgroundColor:  '#0D0D1A',
    borderColor:      'rgba(124,58,237,0.3)',
    borderWidth:      1,
    titleColor:       '#F1F1F8',
    bodyColor:        '#9898B0',
    padding:          12,
    cornerRadius:     10,
  };
}

// ─── THEME TOGGLE ────────────────────────────────────────────────────────────
;(function () {
  const currentTheme = localStorage.getItem('quiznova-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', currentTheme);

  document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.querySelector('[aria-label="Toggle Theme"]');
    if (themeBtn) {
      themeBtn.textContent = currentTheme === 'dark' ? '🌙' : '☀️';
      themeBtn.addEventListener('click', () => {
        const nextTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', nextTheme);
        localStorage.setItem('quiznova-theme', nextTheme);
        themeBtn.textContent = nextTheme === 'dark' ? '🌙' : '☀️';
      });
    }
  });
})();

// ─── GLOBAL EXPORTS ───────────────────────────────────────────────────────────
window.QuizNova = {
  showFlash,
  dismissFlash,
  animateCount,
  copyToClipboard,
};
