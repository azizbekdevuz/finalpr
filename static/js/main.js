/* ─────────────────────────────────────────────────────
   Gabojago — main.js  v3
   Navbar · Flash · Lazy load · Confirm · Motion
───────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ── Navbar: scroll state ─────────────────────────── */
  const nav = document.getElementById('mainNav');
  if (nav) {
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          nav.classList.toggle('scrolled', window.scrollY > 50);
          ticking = false;
        });
        ticking = true;
      }
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ── Mobile nav: close on link tap ──────────────────── */
  const navMenu = document.getElementById('navMenu');
  if (navMenu && nav) {
    navMenu.querySelectorAll('.nav-link:not(.dropdown-toggle)').forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 992 && navMenu.classList.contains('show')) {
          const toggler = nav.querySelector('.navbar-toggler');
          if (toggler) toggler.click();
        }
      });
    });
  }

  /* ── Flash messages auto-dismiss ────────────────────── */
  document.querySelectorAll('.flash-container .alert').forEach(alert => {
    setTimeout(() => {
      try {
        const bsAlert = new mdb.Alert(alert);
        bsAlert.close();
      } catch (e) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(110%)';
        alert.style.transition = 'opacity .3s ease, transform .3s ease';
        setTimeout(() => alert.remove(), 350);
      }
    }, 4000);
  });

  /* ── Lazy load fallback ─────────────────────────────── */
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.dataset.src;
  });

  /* ── Confirm destructive forms ──────────────────────── */
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', function (e) {
      if (!confirm(this.dataset.confirm)) e.preventDefault();
    });
  });

  /* ── OAuth buttons: loading feedback ────────────────── */
  document.querySelectorAll('a.oauth-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      if (this.classList.contains('is-loading')) return;
      this.classList.add('is-loading');
      this.setAttribute('aria-busy', 'true');
      const icon = this.querySelector('i');
      if (icon) {
        icon.dataset.prevClass = icon.className;
        icon.className = 'fas fa-circle-notch fa-spin me-2';
      }
    });
  });

  /* ── Star rating hover (spot forms) ─────────────────── */
  document.querySelectorAll('.star-rating-input label, .star-pick label').forEach(label => {
    label.addEventListener('mouseenter', function () {
      if (!prefersReducedMotion) this.style.transform = 'scale(1.12)';
    });
    label.addEventListener('mouseleave', function () {
      this.style.transform = '';
    });
  });

  /* ── Button press feedback ──────────────────────────── */
  if (!prefersReducedMotion) {
    document.querySelectorAll('.btn, .chat-send-btn, .submit-btn, .oauth-btn, .region-tab-btn').forEach(btn => {
      btn.addEventListener('mousedown', () => { btn.style.transform = 'scale(0.98)'; });
      btn.addEventListener('mouseup', () => { btn.style.transform = ''; });
      btn.addEventListener('mouseleave', () => { btn.style.transform = ''; });
    });
  }

  /* ── Card reveal on scroll ──────────────────────────── */
  if (!prefersReducedMotion && 'IntersectionObserver' in window) {
    const cardSelectors = [
      '.spot-card', '.region-card', '.new-spot-card',
      '.api-spot-card', '.rv-card', '.preview-card', '.course-card'
    ].join(', ');
    const cards = document.querySelectorAll(cardSelectors);

    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.06, rootMargin: '0px 0px -24px 0px' });

    cards.forEach((card, i) => {
      card.classList.add('reveal-card');
      card.style.transitionDelay = `${Math.min(i * 35, 280)}ms`;
      observer.observe(card);
    });
  }
});
