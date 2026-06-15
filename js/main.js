/* =============================================
   CALENDAR QUEEN — Main JavaScript
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initCookieBanner();
  initFeedFilter();
  initCalPreview();
  initSubscribeButtons();
  initFadeIn();
  highlightActiveNavLink();
});

/* ---------- Navigation (hamburger) ---------- */
function initNav() {
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobile-menu');
  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', () => {
    const open = mobileMenu.style.display === 'flex';
    mobileMenu.style.display = open ? 'none' : 'flex';
    hamburger.setAttribute('aria-expanded', String(!open));
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && mobileMenu.style.display === 'flex') {
      mobileMenu.style.display = 'none';
      hamburger.setAttribute('aria-expanded', 'false');
    }
  });
}

function highlightActiveNavLink() {
  const path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    const href = a.getAttribute('href') || '';
    if (href === path || (path === 'index.html' && href === '#')) {
      a.classList.add('active');
    }
  });
}

/* ---------- Cookie Banner ---------- */
function initCookieBanner() {
  const banner = document.getElementById('cookie-banner');
  if (!banner) return;

  if (localStorage.getItem('cq_cookie_consent')) {
    banner.classList.add('hidden');
    return;
  }

  document.getElementById('cookie-accept')?.addEventListener('click', () => {
    localStorage.setItem('cq_cookie_consent', 'accepted');
    banner.classList.add('hidden');
  });
  document.getElementById('cookie-decline')?.addEventListener('click', () => {
    localStorage.setItem('cq_cookie_consent', 'declined');
    banner.classList.add('hidden');
  });
}

/* ---------- Feed Filtering ---------- */
function initFeedFilter() {
  const pills = document.querySelectorAll('.cat-pill[data-cat]');
  const searchInput = document.getElementById('feed-search');
  const cards = document.querySelectorAll('.feed-card[data-cat]');
  const noResults = document.getElementById('no-results');

  if (!pills.length && !searchInput) return;

  let activeCategory = 'all';
  let searchQuery = '';

  function filterCards() {
    let visible = 0;
    cards.forEach(card => {
      const cat = card.getAttribute('data-cat') || '';
      const title = (card.querySelector('.feed-card-title')?.textContent || '').toLowerCase();
      const desc  = (card.querySelector('.feed-card-desc')?.textContent || '').toLowerCase();

      const catMatch = activeCategory === 'all' || cat === activeCategory;
      const queryMatch = !searchQuery ||
        title.includes(searchQuery) || desc.includes(searchQuery);

      if (catMatch && queryMatch) {
        card.style.display = '';
        visible++;
      } else {
        card.style.display = 'none';
      }
    });

    if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
  }

  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeCategory = pill.getAttribute('data-cat');
      filterCards();
    });
    pill.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pill.click(); }
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      searchQuery = searchInput.value.trim().toLowerCase();
      filterCards();
    });
  }
}

/* ---------- Calendar Preview Animation ---------- */
function initCalPreview() {
  const days = document.querySelectorAll('.cal-day.has-event');
  if (!days.length) return;
  let i = 0;
  setInterval(() => {
    days.forEach(d => d.style.background = '');
    if (days[i]) {
      days[i].style.background = 'rgba(245,200,66,0.15)';
      days[i].style.borderRadius = '6px';
    }
    i = (i + 1) % days.length;
  }, 1200);
}

/* ---------- Subscribe Buttons ---------- */
function initSubscribeButtons() {
  document.querySelectorAll('[data-subscribe]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      const feedId = this.getAttribute('data-subscribe');
      const feedTitle = this.getAttribute('data-title') || 'Feed';
      subscribeToFeed(feedId, feedTitle, this);
    });
  });
}

function subscribeToFeed(feedId, title, btn) {
  const icsUrl = `feeds/${feedId}.ics`;

  const original = btn.innerHTML;
  btn.innerHTML = '✓ Abonniert!';
  btn.style.background = 'var(--green-700)';
  btn.disabled = true;

  // Trigger .ics download
  const a = document.createElement('a');
  a.href = icsUrl;
  a.download = `${feedId}.ics`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Show modal with further instructions
  showSubscribeModal(title, icsUrl);

  setTimeout(() => {
    btn.innerHTML = original;
    btn.style.background = '';
    btn.disabled = false;
  }, 3000);
}

function showSubscribeModal(title, icsUrl) {
  const existing = document.getElementById('subscribe-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'subscribe-modal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-label', `${title} abonnieren`);
  modal.style.cssText = `
    position: fixed; inset: 0; background: rgba(26,26,46,0.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 2000; padding: 24px;
  `;
  modal.innerHTML = `
    <div style="background:#fff;border-radius:20px;padding:36px;max-width:440px;width:100%;position:relative;">
      <button onclick="this.closest('#subscribe-modal').remove()"
        aria-label="Schließen"
        style="position:absolute;top:16px;right:16px;width:32px;height:32px;border-radius:50%;border:1px solid var(--gray-200);background:var(--gray-50);cursor:pointer;font-size:18px;color:var(--gray-500);display:flex;align-items:center;justify-content:center;font-family:var(--font-body);">×</button>
      <div style="font-size:32px;margin-bottom:12px;">📅</div>
      <h2 style="font-size:20px;font-weight:600;color:var(--violet-900);margin-bottom:8px;">„${title}" abonnieren</h2>
      <p style="font-size:14px;color:var(--gray-500);line-height:1.6;margin-bottom:24px;">
        Wähle deinen Kalender und folge den Anweisungen:
      </p>
      <div style="display:flex;flex-direction:column;gap:10px;">
        <a href="${icsUrl}" style="display:flex;align-items:center;gap:12px;background:var(--gray-50);border:1px solid var(--gray-200);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--gray-700);font-size:14px;font-weight:500;transition:background 0.2s;" onmouseover="this.style.background='var(--violet-50)'" onmouseout="this.style.background='var(--gray-50)'">
          <span style="font-size:22px;">🍎</span>
          <div><div style="font-weight:600;">Apple Calendar</div><div style="font-size:12px;color:var(--gray-400);">.ics Datei öffnen → Zum Kalender hinzufügen</div></div>
        </a>
        <a href="https://calendar.google.com/calendar/r/settings/addbyurl?url=${encodeURIComponent(window.location.origin + '/' + icsUrl)}" target="_blank" rel="noopener" style="display:flex;align-items:center;gap:12px;background:var(--gray-50);border:1px solid var(--gray-200);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--gray-700);font-size:14px;font-weight:500;transition:background 0.2s;" onmouseover="this.style.background='var(--violet-50)'" onmouseout="this.style.background='var(--gray-50)'">
          <span style="font-size:22px;">🗓️</span>
          <div><div style="font-weight:600;">Google Calendar</div><div style="font-size:12px;color:var(--gray-400);">Direkt in Google Kalender hinzufügen</div></div>
        </a>
        <a href="${icsUrl}" style="display:flex;align-items:center;gap:12px;background:var(--gray-50);border:1px solid var(--gray-200);border-radius:12px;padding:14px 16px;text-decoration:none;color:var(--gray-700);font-size:14px;font-weight:500;transition:background 0.2s;" onmouseover="this.style.background='var(--violet-50)'" onmouseout="this.style.background='var(--gray-50)'">
          <span style="font-size:22px;">📧</span>
          <div><div style="font-weight:600;">Outlook</div><div style="font-size:12px;color:var(--gray-400);">.ics öffnen oder per „Kalender importieren" in Outlook</div></div>
        </a>
      </div>
      <p style="font-size:12px;color:var(--gray-400);margin-top:16px;text-align:center;">Die .ics-Datei wurde automatisch heruntergeladen.</p>
    </div>
  `;

  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
  document.addEventListener('keydown', function handler(e) {
    if (e.key === 'Escape') { modal.remove(); document.removeEventListener('keydown', handler); }
  });

  document.body.appendChild(modal);
  modal.querySelector('button').focus();
}

/* ---------- Fade-in on scroll ---------- */
function initFadeIn() {
  const els = document.querySelectorAll('.fade-in');
  if (!els.length) return;
  if (!('IntersectionObserver' in window)) {
    els.forEach(el => el.classList.add('visible'));
    return;
  }
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        obs.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
  els.forEach(el => obs.observe(el));
}
