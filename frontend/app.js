(() => {
  // ---------- i18n ----------
  const I18N = {
    en: {
      brand: "Veeza AI", tagline: "European visa assistant for Egyptians",
      historyBtn: "History", newBtn: "↺ New session", planTitle: "Your Visa Plan",
      pdfBtn: "⬇ PDF", historyTitle: "Your saved plans", inputPh: "Tell me about your trip…",
      welcomeTitle: "مرحبا / Welcome 👋",
      welcomeText: "I'm Veeza — your visa assistant. I'll research the latest requirements from official embassy and visa-centre websites, ask you a few questions about your situation, and then build you a complete, step-by-step application plan with your documents, costs and timeline.",
      welcomeHint: "To get started, tell me what you're planning. For example:",
      welcomeExample: "\u201CI want to travel to Italy for a week of tourism next September, me and my wife.\u201D",
      statusBusy: "Working on it…",
      overviewTitle: "Overview", chancesTitle: "Your chances", weakTitle: "Watch out for these",
      timelineTitle: "Timeline", stepsTitle: "Step-by-step process", docsTitle: "Document checklist",
      costsTitle: "Estimated costs", tipsTitle: "Tips for your case", sourcesTitle: "Official sources",
      docProgress: "Documents ready", docReady: "All documents checked — you're ready to apply!", noDocsYet: "Check items as you gather them.",
      egpNote: "≈ EGP",
      totalLabel: "Total estimate",
      origBadge: "Original", trBadge: "Translated", notarizedBadge: "Notarized",
      planNote: "This plan is generated from current public information for research purposes. Visa approval is always at the embassy's discretion — confirm everything on the official websites before paying or submitting.",
      historyEmpty: "No saved plans yet. Your plans are stored privately in your browser.",
      planSaved: "Plan saved to history.", planShare: "Download as PDF",
      notApplicable: "not applicable",
    },
    ar: {
      brand: "فيزا AI", tagline: "مساعد التأشيرات الأوروبية للمصريين",
      historyBtn: "السجل", newBtn: "↺ جلسة جديدة", planTitle: "خطة التأشيرة الخاصة بك",
      pdfBtn: "⬇ PDF", historyTitle: "الخطط المحفوظة", inputPh: "احكِ لي عن رحلتك…",
      welcomeTitle: "مرحبا / Welcome 👋",
      welcomeText: "أنا فيزا — مساعدك للحصول على التأشيرة. سأبحث عن أحدث المتطلبات من المواقع الرسمية للسفارات ومراكز التأشيرات، وأسألك بعض الأسئلة عن حالتك، ثم أبني لك خطة كاملة خطوة بخطوة تشمل المستندات والتكاليف والجدول الزمني.",
      welcomeHint: "لتبدأ، أخبرني عن خطتك. على سبيل المثال:",
      welcomeExample: "«أريد السفر إلى إيطاليا لمدة أسبوع سياحة في سبتمبر القادم، أنا وزوجتي».",
      statusBusy: "أعمل على ذلك…",
      overviewTitle: "نظرة عامة", chancesTitle: "فرصك", weakTitle: "انتبه لهذه النقاط",
      timelineTitle: "الجدول الزمني", stepsTitle: "الخطوات بالتفصيل", docsTitle: "قائمة المستندات",
      costsTitle: "التكاليف المتوقعة", tipsTitle: "نصائح لحالتك", sourcesTitle: "المصادر الرسمية",
      docProgress: "المستندات الجاهزة", docReady: "تم تجهيز كل المستندات — أنت جاهز للتقديم!", noDocsYet: "حدد البنود عند تجهيزها.",
      egpNote: "≈ جنيه",
      totalLabel: "الإجمالي المتوقع",
      origBadge: "الأصل", trBadge: "مترجم", notarizedBadge: "موثق",
      planNote: "هذه الخطة مبنية على معلومات عامة حديثة لأغراض البحث. قرار التأشيرة دائمًا بيد السفارة — تأكد من كل شيء على المواقع الرسمية قبل الدفع أو التقديم.",
      historyEmpty: "لا توجد خطط محفوظة بعد. خططك محفوظة بشكل خاص في متصفحك.",
      planSaved: "تم حفظ الخطة في السجل.", planShare: "تحميل PDF",
      notApplicable: "غير قابل للتطبيق",
    }
  };

  let lang = localStorage.getItem('veeza_lang') || 'en';
  const t = (key) => (I18N[lang] && I18N[lang][key]) ?? I18N.en[key] ?? key;

  // ---------- State ----------
  let sessionId = localStorage.getItem('veeza_session') || null;
  let busy = false;
  let currentPlan = null;
  let currentPlanTs = null;
  let egpRate = null;

  const $ = (id) => document.getElementById(id);
  const messagesEl = $('messages'), form = $('chatForm'), input = $('input');
  const sendBtn = $('sendBtn'), resetBtn = $('resetBtn'), langBtn = $('langBtn');
  const historyBtn = $('historyBtn'), planPane = $('planPane'), planType = $('planType');
  const planBody = $('planBody'), pdfBtn = $('pdfBtn');
  const historyModal = $('historyModal'), historyList = $('historyList');
  const historyClose = $('historyClose');

  const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const linkify = (text) => esc(text).replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');

  // ---------- Language ----------
  function applyLang() {
    const dir = lang === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
      el.textContent = t(el.dataset.i18n);
    });
    const ph = document.querySelector('[data-i18n-ph]');
    if (ph) ph.placeholder = t('inputPh');
    langBtn.textContent = lang === 'ar' ? 'EN' : 'العربية';
    if (currentPlan) renderPlan(currentPlan);
  }
  langBtn.addEventListener('click', () => {
    lang = lang === 'en' ? 'ar' : 'en';
    localStorage.setItem('veeza_lang', lang);
    applyLang();
  });

  // ---------- Chat UI ----------
  function addMsg(text, who) {
    const div = document.createElement('div');
    div.className = `msg ${who}`;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerHTML = who === 'user' ? esc(text) : linkify(text);
    div.appendChild(bubble);
    messagesEl.appendChild(div);
    scrollDown();
    return div;
  }

  function addStatus() {
    const div = document.createElement('div');
    div.className = 'msg agent';
    div.innerHTML = `<div class="bubble"><span class="status-line"><span class="dot"></span><span class="status-text">${esc(t('statusBusy'))}</span></span></div>`;
    messagesEl.appendChild(div);
    scrollDown();
    return div;
  }

  function setStatus(div, text) {
    const el = div.querySelector('.status-text');
    if (el) el.textContent = text;
  }

  function scrollDown() { messagesEl.scrollTop = messagesEl.scrollHeight; }

  function showWelcome() {
    const div = document.createElement('div');
    div.className = 'msg agent';
    div.innerHTML = `<div class="bubble welcome">
      <h2>${esc(t('welcomeTitle'))}</h2>
      <p>${esc(t('welcomeText'))}</p>
      <p class="hint">${esc(t('welcomeHint'))}<br><em>${esc(t('welcomeExample'))}</em></p>
    </div>`;
    messagesEl.appendChild(div);
  }

  // ---------- SSE streaming ----------
  async function send(text) {
    if (busy || !text.trim()) return;
    busy = true;
    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;
    addMsg(text.trim(), 'user');

    const statusEl = addStatus();
    let finalEvent = null;
    try {
      const res = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: text.trim() }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const handleLine = (line) => {
        if (!line.startsWith('data: ')) return;
        const payload = line.slice(6).trim();
        if (payload === '[DONE]') return;
        let ev;
        try { ev = JSON.parse(payload); } catch { return; }
        if (ev.session_id) {
          sessionId = ev.session_id;
          localStorage.setItem('veeza_session', sessionId);
        }
        if (ev.type === 'status') {
          setStatus(statusEl, ev.text || t('statusBusy'));
        } else if (ev.type === 'question' || ev.type === 'message' || ev.type === 'plan') {
          finalEvent = ev;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop();
        for (const part of parts) handleLine(part);
      }
      handleLine(buffer);

      statusEl.remove();
      if (finalEvent && finalEvent.type === 'question') {
        addMsg(finalEvent.reply, 'agent');
      } else if (finalEvent && finalEvent.type === 'plan') {
        addMsg(finalEvent.reply, 'agent');
        renderPlan(finalEvent.plan);
      } else if (finalEvent) {
        addMsg(finalEvent.reply, 'agent');
      } else {
        throw new Error('no final event');
      }
    } catch (e) {
      statusEl.remove();
      addMsg(lang === 'ar'
        ? 'عذرًا، حدث خطأ. حاول مرة أخرى.'
        : 'Sorry, something went wrong. Please try again.', 'agent');
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener('submit', (e) => { e.preventDefault(); send(input.value); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input.value); }
  });
  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 130) + 'px';
  });

  document.querySelectorAll('.chip').forEach((chip) => {
    chip.addEventListener('click', () => send(chip.dataset.example));
  });

  // ---------- Exchange rate ----------
  async function loadRate() {
    try {
      const r = await fetch('/api/rate');
      const data = await r.json();
      egpRate = data.eur_to_egp;
    } catch { egpRate = null; }
  }

  function toEGP(valueStr) {
    if (!egpRate) return null;
    const m = String(valueStr || '').replace(/[^\d.,]/g, '').match(/[\d.,]+/);
    if (!m) return null;
    const num = parseFloat(m[0].replace(/,/g, ''));
    if (!isFinite(num) || num <= 0) return null;
    return Math.round(num * egpRate).toLocaleString('en-US');
  }

  // ---------- Plan rendering ----------
  const badge = (label, cls) => `<span class="badge ${cls}">${label}</span>`;

  const costsStore = (planTs) => `veeza_checks_${sessionId || 'guest'}_${planTs}`;

  function getChecks(planTs) {
    try { return JSON.parse(localStorage.getItem(costsStore(planTs))) || {}; } catch { return {}; }
  }
  function setCheck(planTs, idx, checked) {
    const key = costsStore(planTs);
    const checks = getChecks(planTs);
    if (checked) checks[idx] = true; else delete checks[idx];
    localStorage.setItem(key, JSON.stringify(checks));
    renderProgress(planTs);
  }

  function renderProgress(planTs) {
    if (!currentPlan || !currentPlan.documents) return;
    const total = currentPlan.documents.length;
    const done = Object.keys(getChecks(planTs)).length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    const fill = document.querySelector('.progress-fill');
    const label = document.querySelector('.progress-label');
    const ready = document.querySelector('.progress-ready');
    if (fill) fill.style.width = pct + '%';
    if (label) label.textContent = `${done}/${total} ${t('docProgress')} · ${pct}%`;
    if (ready) ready.classList.toggle('show', total > 0 && done === total);
  }

  function renderPlan(plan) {
    currentPlan = plan;
    currentPlanTs = plan._ts || Date.now();
    planType.textContent = plan.visa_type || 'Visa plan';
    planPane.classList.remove('hidden');
    let html = '';

    // Progress tracker
    const totalDocs = (plan.documents || []).length;
    const doneDocs = Object.keys(getChecks(currentPlanTs)).length;
    const pct = totalDocs ? Math.round((doneDocs / totalDocs) * 100) : 0;
    html += `<div class="checklist-progress">
      <div class="progress-row"><span class="progress-label">${doneDocs}/${totalDocs} ${t('docProgress')} · ${pct}%</span></div>
      <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
      <div class="progress-ready">✅ ${t('docReady')}</div>
    </div>`;

    if (plan.visa_summary) {
      html += `<div class="plan-section"><h4>${t('overviewTitle')}</h4><div class="summary-card">${linkify(plan.visa_summary)}</div></div>`;
    }

    // Chances + weak points (our differentiator)
    if (plan.chances) {
      const badgeCls = ['good', 'challenging', 'fair'].some((w) => String(plan.chances).toLowerCase().includes(w))
        ? (String(plan.chances).toLowerCase().includes('good') ? 'Good'
           : String(plan.chances).toLowerCase().includes('challeng') ? 'Challenging' : 'Fair')
        : 'Fair';
      html += `<div class="plan-section">
        <h4>${t('chancesTitle')}</h4>
        <div class="chances-row"><span class="chances-label">${lang === 'ar' ? 'احتمالية النجاح' : 'Approval likelihood'}</span>
        <span class="chance-badge ${badgeCls}">${esc(plan.chances)}</span></div>`;
      if (plan.weak_points && plan.weak_points.length) {
        html += `<div class="weak-list">`;
        for (const w of plan.weak_points) html += `<div class="weak-item">${esc(w)}</div>`;
        html += `</div>`;
      }
      html += `</div>`;
    }

    if (plan.timeline) {
      html += `<div class="plan-section"><h4>${t('timelineTitle')}</h4><div class="timeline-card">${linkify(plan.timeline)}</div></div>`;
    }

    if (plan.steps && plan.steps.length) {
      html += `<div class="plan-section"><h4>${t('stepsTitle')}</h4>`;
      for (const s of plan.steps) {
        html += `<div class="step">
          <div class="step-num">${s.step}</div>
          <div class="step-body">
            <b>${esc(s.title)}</b>
            <div class="detail">${linkify(s.detail)}</div>
            ${s.when ? `<div class="when">⏱ ${esc(s.when)}</div>` : ''}
          </div>
        </div>`;
      }
      html += `</div>`;
    }

    if (plan.documents && plan.documents.length) {
      const checks = getChecks(currentPlanTs);
      html += `<div class="plan-section"><h4>${t('docsTitle')}</h4>`;
      plan.documents.forEach((d, idx) => {
        const checked = !!checks[idx];
        const parts = [];
        if (d.original) parts.push(badge(t('origBadge'), 'or'));
        if (d.translated) parts.push(badge(t('trBadge'), 'tr'));
        if (d.notarized) parts.push(badge(t('notarizedBadge'), 'no'));
        html += `<div class="doc-row ${checked ? 'checked' : ''}">
          <label class="doc-check">
            <input type="checkbox" data-idx="${idx}" ${checked ? 'checked' : ''}>
            <span><b>${esc(d.item)}</b>
              ${d.why ? `<span class="why">${esc(d.why)}</span>` : ''}
              ${parts.length ? `<span class="badges">${parts.join('')}</span>` : ''}
            </span>
          </label>
        </div>`;
      });
      html += `</div>`;
    }

    const c = plan.costs || {};
    const rows = [
      ['Visa fee', c.visa_fee], ['Visa-centre service fee', c.service_fee],
      ['Travel insurance', c.insurance], ['Flights', c.flights],
      ['Accommodation', c.accommodation],
    ].filter(([, v]) => v && v !== t('notApplicable') && v !== 'not applicable');
    if (rows.length) {
      const labelMap = {
        'Visa fee': lang === 'ar' ? 'رسوم التأشيرة' : 'Visa fee',
        'Visa-centre service fee': lang === 'ar' ? 'رسوم مركز التأشيرات' : 'Visa-centre service fee',
        'Travel insurance': lang === 'ar' ? 'التأمين الصحي للسفر' : 'Travel insurance',
        'Flights': lang === 'ar' ? 'الطيران' : 'Flights',
        'Accommodation': lang === 'ar' ? 'الإقامة' : 'Accommodation',
      };
      html += `<div class="plan-section"><h4>${t('costsTitle')}</h4><table class="cost-table">`;
      for (const [label, val] of rows) {
        const egp = toEGP(val);
        html += `<tr><td>${esc(labelMap[label] || label)}</td><td>≈ ${esc(val)}${egp ? `<span class="egp">${t('egpNote')} ${egp}</span>` : ''}</td></tr>`;
      }
      if (c.total_estimate) {
        const egp = toEGP(c.total_estimate);
        html += `<tr class="total"><td>${t('totalLabel')}</td><td>≈ ${esc(c.total_estimate)}${egp ? `<span class="egp">${t('egpNote')} ${egp}</span>` : ''}</td></tr>`;
      }
      html += `</table></div>`;
    }

    if (plan.tips && plan.tips.length) {
      html += `<div class="plan-section"><h4>${t('tipsTitle')}</h4>`;
      for (const tip of plan.tips) html += `<div class="tip">${esc(tip)}</div>`;
      html += `</div>`;
    }

    if (plan.sources && plan.sources.length) {
      html += `<div class="plan-section"><h4>${t('sourcesTitle')}</h4><div class="sources">`;
      for (const s of plan.sources) html += `<a href="${esc(s)}" target="_blank" rel="noopener">${esc(s)}</a>`;
      html += `</div></div>`;
    }

    html += `<div class="plan-note">${t('planNote')}</div>`;

    planBody.innerHTML = html;
    renderProgress(currentPlanTs);

    planBody.querySelectorAll('.doc-check input[type="checkbox"]').forEach((cb) => {
      cb.addEventListener('change', () => {
        const idx = parseInt(cb.dataset.idx, 10);
        cb.closest('.doc-row').classList.toggle('checked', cb.checked);
        setCheck(currentPlanTs, idx, cb.checked);
      });
    });

    if (window.innerWidth <= 900) planPane.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ---------- History ----------
  function getHistory() {
    try { return JSON.parse(localStorage.getItem('veeza_history')) || []; } catch { return []; }
  }
  function saveToHistory(plan) {
    const entry = { ts: Date.now(), visa_type: plan.visa_type || 'Plan', plan: Object.assign({}, plan, { _ts: Date.now() }) };
    const hist = getHistory();
    hist.unshift(entry);
    localStorage.setItem('veeza_history', JSON.stringify(hist.slice(0, 20)));
  }
  function renderHistory() {
    const hist = getHistory();
    historyList.innerHTML = hist.length ? '' : `<div class="history-empty">${t('historyEmpty')}</div>`;
    hist.forEach((h) => {
      const item = document.createElement('div');
      item.className = 'history-item';
      const date = new Date(h.ts).toLocaleDateString(lang === 'ar' ? 'ar-EG' : 'en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
      item.innerHTML = `<div><b>${esc(h.visa_type)}</b><span>${date}</span></div><div>↩</div>`;
      item.addEventListener('click', () => { renderPlan(h.plan); historyModal.classList.add('hidden'); });
      historyList.appendChild(item);
    });
  }
  historyBtn.addEventListener('click', () => { renderHistory(); historyModal.classList.remove('hidden'); });
  historyClose.addEventListener('click', () => historyModal.classList.add('hidden'));
  historyModal.addEventListener('click', (e) => { if (e.target === historyModal) historyModal.classList.add('hidden'); });

  // ---------- PDF export ----------
  pdfBtn.addEventListener('click', () => {
    const paneVisible = !planPane.classList.contains('hidden');
    if (!paneVisible && currentPlan) { renderPlan(currentPlan); }
    window.print();
  });

  // ---------- Reset ----------
  resetBtn.addEventListener('click', async () => {
    if (sessionId) {
      await fetch('/api/reset', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ session_id: sessionId }) }).catch(() => {});
    }
    sessionId = null;
    localStorage.removeItem('veeza_session');
    currentPlan = null;
    messagesEl.innerHTML = '';
    planPane.classList.add('hidden');
    planBody.innerHTML = '';
    planType.textContent = '';
    busy = false;
    showWelcome();
    input.focus();
  });

  // ---------- Init ----------
  applyLang();
  loadRate();
  showWelcome();
  input.focus();
})();
