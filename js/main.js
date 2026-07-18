'use strict';

document.addEventListener('DOMContentLoaded', () => {
  initNav();
  initCookieBanner();
  initCalendarWidget();
  initFeedFilter();
  initSubscribeButtons();
  initFaqAccordion();
  initFadeIn();
});

function initNav() {
  const btn = document.getElementById('hamburger');
  const menu = document.getElementById('mobile-menu');
  if (!btn || !menu) return;
  btn.addEventListener('click', () => {
    const open = menu.style.display === 'flex';
    menu.style.display = open ? 'none' : 'flex';
    btn.setAttribute('aria-expanded', String(!open));
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.style.display === 'flex') {
      menu.style.display = 'none';
      btn.setAttribute('aria-expanded', 'false');
      btn.focus();
    }
  });
  const path = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a, .mobile-menu a').forEach(a => {
    const href = (a.getAttribute('href') || '').split('#')[0].split('?')[0];
    if (href === path || (path === '' && href === 'index.html')) {
      a.setAttribute('aria-current', 'page');
    }
  });
}

function initCookieBanner() {
  const banner = document.getElementById('cookie-banner');
  if (!banner) return;
  if (localStorage.getItem('cq_consent')) { banner.classList.add('hidden'); return; }
  document.getElementById('cookie-accept')?.addEventListener('click', () => {
    localStorage.setItem('cq_consent', 'accepted');
    banner.classList.add('hidden');
  });
  document.getElementById('cookie-decline')?.addEventListener('click', () => {
    localStorage.setItem('cq_consent', 'essential');
    banner.classList.add('hidden');
  });
}

function initCalendarWidget() {
  const daysEl  = document.getElementById('cal-days');
  const chipsEl = document.getElementById('cal-chips');
  const monthEl = document.getElementById('cal-month-label');
  if (!daysEl) return;

  const MONTHS = ['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'];
  const EVENTS = {
    6: { 10:[{t:'Vollmond',s:'Mondphasen-Feed',c:'#E68B71'}], 19:[{t:'Flohmarkt Mauerpark',s:'Berlin Events',c:'#C4C1BE'}], 20:[{t:'Wachstumsschub – Woche 12',s:'Babyjahr-Feed',c:'#E68B71'}], 25:[{t:'Neumond',s:'Mondphasen-Feed',c:'#C4C1BE'}] },
    7: { 1:[{t:'Brombeeren – Erntezeit',s:'Kräuter Berlin',c:'#C4C1BE'}], 9:[{t:'Vollmond – Störmond',s:'Mondphasen-Feed',c:'#E68B71'}], 11:[{t:'Perseiden – Meteorschauer',s:'Astronomie-Feed',c:'#C4C1BE'}], 23:[{t:'Neumond',s:'Mondphasen-Feed',c:'#C4C1BE'}] },
    8: { 7:[{t:'Vollmond – Erntemon',s:'Mondphasen-Feed',c:'#E68B71'}], 13:[{t:'Flohmarkt Mauerpark',s:'Berlin Events',c:'#C4C1BE'}], 21:[{t:'Neumond',s:'Mondphasen-Feed',c:'#C4C1BE'}] }
  };

  const today = new Date(2026, 6, 18);
  let cur = new Date(today.getFullYear(), today.getMonth(), 1);

  function render() {
    const m = cur.getMonth(), y = cur.getFullYear();
    monthEl.textContent = MONTHS[m] + ' ' + y;

    const firstDay = new Date(y, m, 1).getDay();
    const startOffset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(y, m + 1, 0).getDate();
    const daysInPrev  = new Date(y, m, 0).getDate();
    const monthEvs    = EVENTS[m] || {};

    daysEl.innerHTML = '';
    for (let i = startOffset - 1; i >= 0; i--) {
      const d = document.createElement('div');
      d.className = 'cal-day other-month';
      d.textContent = daysInPrev - i;
      daysEl.appendChild(d);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      const d = document.createElement('div');
      d.className = 'cal-day';
      if (y === today.getFullYear() && m === today.getMonth() && day === today.getDate()) d.classList.add('today');
      if (monthEvs[day]) d.classList.add('has-event');
      d.textContent = day;
      daysEl.appendChild(d);
    }
    const remaining = daysEl.children.length % 7 === 0 ? 0 : 7 - (daysEl.children.length % 7);
    for (let i = 1; i <= remaining; i++) {
      const d = document.createElement('div');
      d.className = 'cal-day other-month';
      d.textContent = i;
      daysEl.appendChild(d);
    }

    chipsEl.innerHTML = '';
    Object.entries(monthEvs).sort((a,b) => +a[0] - +b[0]).slice(0,4).forEach(([day, items]) => {
      items.forEach(ev => {
        const chip = document.createElement('div');
        chip.className = 'cal-chip';
        chip.style.background = ev.c === '#E68B71' ? 'rgba(230,139,113,0.12)' : 'rgba(196,193,190,0.2)';
        chip.style.color = ev.c === '#E68B71' ? '#C0522F' : '#444441';
        const dot = `<span style="width:7px;height:7px;border-radius:50%;background:${ev.c};flex-shrink:0;display:inline-block;margin-top:1px"></span>`;
        chip.innerHTML = `${dot}<span style="font-weight:600;min-width:22px">${day}.</span>${ev.t} <span style="opacity:.55;font-size:10px;margin-left:auto">· ${ev.s}</span>`;
        chipsEl.appendChild(chip);
      });
    });
  }

  document.getElementById('cal-prev')?.addEventListener('click', () => { cur = new Date(cur.getFullYear(), cur.getMonth() - 1, 1); render(); });
  document.getElementById('cal-next')?.addEventListener('click', () => { cur = new Date(cur.getFullYear(), cur.getMonth() + 1, 1); render(); });
  render();
}

function initFeedFilter() {
  const pills  = document.querySelectorAll('.cat-pill[data-cat]');
  const search = document.getElementById('feed-search');
  const cards  = document.querySelectorAll('.feed-card[data-cat]');
  const noRes  = document.getElementById('no-results');
  const label  = document.getElementById('count-label');
  if (!pills.length && !search) return;

  let activeCat = 'all', query = '';

  function filter() {
    let visible = 0;
    cards.forEach(card => {
      const catOk   = activeCat === 'all' || card.getAttribute('data-cat') === activeCat;
      const queryOk = !query || (card.textContent || '').toLowerCase().includes(query);
      const show = catOk && queryOk;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    if (noRes) noRes.style.display = visible === 0 ? 'block' : 'none';
    if (label) label.textContent = `${visible} Feed${visible !== 1 ? 's' : ''} angezeigt`;
  }

  pills.forEach(p => {
    p.addEventListener('click', () => {
      pills.forEach(x => { x.classList.remove('active'); x.setAttribute('aria-pressed','false'); });
      p.classList.add('active'); p.setAttribute('aria-pressed','true');
      activeCat = p.getAttribute('data-cat');
      filter();
    });
  });
  search?.addEventListener('input', () => { query = search.value.trim().toLowerCase(); filter(); });
  filter();
}

function initSubscribeButtons() {
  document.querySelectorAll('[data-subscribe]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault(); e.stopPropagation();
      showSubscribeModal(el.getAttribute('data-subscribe'), el.getAttribute('data-title') || 'Feed');
    });
  });
}

function showSubscribeModal(feedId, title) {
  document.getElementById('cq-modal')?.remove();
  const icsUrl = `feeds/${feedId}.ics`;
  const gcal   = `https://calendar.google.com/calendar/r/settings/addbyurl?url=${encodeURIComponent(window.location.origin + '/' + icsUrl)}`;

  const overlay = document.createElement('div');
  overlay.id = 'cq-modal';
  overlay.className = 'modal-overlay';
  overlay.setAttribute('role','dialog');
  overlay.setAttribute('aria-modal','true');
  overlay.setAttribute('aria-label', title + ' abonnieren');
  overlay.innerHTML = `
    <div class="modal-box">
      <button class="modal-close" aria-label="Schließen">×</button>
      <p class="eyebrow" style="margin-bottom:10px">Feed abonnieren</p>
      <h2 style="font-size:20px;font-weight:600;letter-spacing:-.02em;margin-bottom:8px;color:var(--black)">${title}</h2>
      <p style="font-size:13px;color:var(--black-soft);line-height:1.6;margin-bottom:20px">Wähle deine Kalender-App:</p>
      <a href="${icsUrl}" download class="modal-option">
        <div class="modal-option-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8m-4-4v4"/></svg></div>
        <div><div class="modal-option-title">Apple Calendar</div><div class="modal-option-sub">.ics herunterladen → In Kalender öffnen</div></div>
      </a>
      <a href="${gcal}" target="_blank" rel="noopener noreferrer" class="modal-option">
        <div class="modal-option-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
        <div><div class="modal-option-title">Google Calendar</div><div class="modal-option-sub">Direkt zu Google Kalender hinzufügen</div></div>
      </a>
      <a href="${icsUrl}" download class="modal-option">
        <div class="modal-option-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></div>
        <div><div class="modal-option-title">Outlook</div><div class="modal-option-sub">.ics herunterladen → In Outlook importieren</div></div>
      </a>
      <p style="font-size:11px;color:var(--black-soft);margin-top:14px;text-align:center">Kompatibel mit Apple, Google und Outlook</p>
    </div>`;

  overlay.querySelector('.modal-close').addEventListener('click', () => overlay.remove());
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  const esc = e => { if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', esc); } };
  document.addEventListener('keydown', esc);
  document.body.appendChild(overlay);
  overlay.querySelector('.modal-close').focus();
}

function initFaqAccordion() {
  document.querySelectorAll('.faq-q').forEach(btn => {
    btn.addEventListener('click', () => {
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!expanded));
      document.getElementById(btn.getAttribute('aria-controls'))?.classList.toggle('open', !expanded);
    });
  });
}

function initFadeIn() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); } });
  }, { threshold: 0.1 });
  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
}
