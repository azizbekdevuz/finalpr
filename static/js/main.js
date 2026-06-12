/* ─────────────────────────────────────────────────────
   Korea Travel Guide — main.js  v2
   Navbar scroll · Flash dismiss · Lazy load
   Confirm forms · Star rating · Card animations
───────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', function () {

  /* ── Navbar: 스크롤 시 배경 강화 ──────────────────── */
  const nav = document.getElementById('mainNav');
  if (nav) {
    let ticking = false;
    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          if (window.scrollY > 50) {
            nav.classList.add('scrolled');
          } else {
            nav.classList.remove('scrolled');
            nav.style.background = '';
          }
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  /* ── Flash 메시지 자동 닫기 (4초) ─────────────────── */
  const alerts = document.querySelectorAll('.flash-container .alert');
  alerts.forEach(alert => {
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

  /* ── 이미지 Lazy Load 폴백 ─────────────────────────── */
  document.querySelectorAll('img[data-src]').forEach(img => {
    img.src = img.dataset.src;
  });

  /* ── 삭제 확인 폼 ──────────────────────────────────── */
  document.querySelectorAll('form[data-confirm]').forEach(form => {
    form.addEventListener('submit', function (e) {
      if (!confirm(this.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  /* ── 별점 입력 시각 피드백 ─────────────────────────── */
  const starLabels = document.querySelectorAll('.star-rating-input label');
  starLabels.forEach(label => {
    label.addEventListener('mouseenter', function () {
      this.style.transform = 'scale(1.18)';
    });
    label.addEventListener('mouseleave', function () {
      this.style.transform = '';
    });
  });

  /* ── 페이지 진입 애니메이션 ────────────────────────── */
  const cards = document.querySelectorAll('.spot-card, .region-card, .new-spot-card');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });

    cards.forEach((card, i) => {
      card.style.opacity = '0';
      card.style.transform = 'translateY(24px)';
      card.style.transition = `opacity .45s cubic-bezier(.16,1,.3,1) ${i * 40}ms,
                               transform .45s cubic-bezier(.16,1,.3,1) ${i * 40}ms`;
      observer.observe(card);
    });
  }

});
