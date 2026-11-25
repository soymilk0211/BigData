/* Apple 風格版：資料共用 ../run.js（真實執行 test-logs/B-4），步驟與手帳版相同。 */
(() => {
  const RUN = window.DEMO_RUN;
  if (!RUN) return;

  const params = new URLSearchParams(location.search);
  const startStep = params.has("step") ? Number(params.get("step")) : null;
  const autoplay = params.get("play") !== "0" && startStep === null && params.get("paused") !== "1";
  const speed = Math.max(0.4, Math.min(2, Number(params.get("speed") || 1)));
  if (params.get("record") === "1") document.body.classList.add("record");
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const SPRING = getComputedStyle(document.documentElement).getPropertyValue("--spring").trim() || "ease-out";

  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  // run.js 有一個簡體字「过」，這裡顯示時修正，不改原檔（手帳版共用）。
  const zh = (s) => esc(s).replace(/过/g, "過");

  const bar = $("bar");
  const question = $("question");
  const invoke = $("invoke");
  const team = $("team");
  const tiles = $("tiles");
  const work = $("work");
  const report = $("report");
  const btnReplay = $("btn-replay");
  const btnPause = $("btn-pause");
  const btnNext = $("btn-next");

  $("question-text").innerHTML = zh(RUN.question);
  $("skill-name").textContent = RUN.skill.name;
  $("skill-title").textContent = RUN.skill.title;
  $("skill-args").innerHTML = zh(RUN.skill.invoked_with);
  $("report-title").textContent = RUN.report.title;
  $("report-conclusion").innerHTML = zh(RUN.report.conclusion);
  $("report-summary").innerHTML = RUN.report.summary
    .map((s) => `<div class="${s.label === "風險" ? "risk" : ""}"><dt>${zh(s.label)}</dt><dd>${zh(s.text)}</dd></div>`)
    .join("");
  $("report-charts").innerHTML = RUN.report.charts
    .map((c) => `<figure><img src="../${esc(c.src)}" alt="${esc(c.alt)}" width="1050" height="600" loading="lazy"><figcaption>${zh(c.alt)}</figcaption></figure>`)
    .join("");
  $("colophon").innerHTML =
    `畫面重播自 Claude Code CLI 的真實執行 <code>${esc(RUN.source.log)}</code>，` +
    `執行編號 ${esc(RUN.source.run_id)}，${esc(RUN.source.recorded_at)}，共 ${RUN.source.turns} 回合、約 ${RUN.source.duration_sec} 秒，審查 ${esc(RUN.source.review)}。` +
    `數字與結論都來自那次產出，沒有另外編造。`;

  tiles.innerHTML = RUN.agents
    .map((a) => `<button type="button" class="tile${a.optional ? " optional" : ""}" id="tile-${a.id}" data-agent="${a.id}">
        <span class="no" aria-hidden="true">${a.no}</span>
        <span class="name">${zh(a.name)}</span>
        <span class="en">${a.name_en}</span>
        <span class="brief">${zh(a.brief)}</span>
        <span class="state" data-state>${zh(a.wait)}</span>
      </button>`)
    .join("");

  /* 步驟：0 空白，1 提問，2 啟動 Skill，3 角色格子，4–8 各角色，9 報告 */
  const AGENT_START = 4;
  const LAST = AGENT_START + RUN.agents.length; /* 9 */
  const LABELS = ["準備", "同學提問", "喚起 Skill", "叫出五個角色", ...RUN.agents.map((a) => a.name), "最終報告"];
  const holds = [0, 2200, 1600, 1600, 4200, 4200, 4800, 4800, 3600, 0].map((ms) => Math.round(ms / speed));
  let step = 0;
  let playing = false;
  let timer = null;
  let shownAgent = null;

  const clearTimer = () => { clearTimeout(timer); timer = null; };

  function reveal(el, block = "nearest") {
    el.scrollIntoView({ block, behavior: reduceMotion.matches ? "auto" : "smooth" });
  }

  /* 換角色時，內容從下方輕輕浮上；減少動態時只淡入 */
  function settleIn(nodes) {
    nodes.forEach((n, i) => n.animate(
      reduceMotion.matches
        ? [{ opacity: 0 }, { opacity: 1 }]
        : [{ opacity: 0, transform: "translateY(10px)" }, { opacity: 1, transform: "none" }],
      { duration: reduceMotion.matches ? 200 : 600, delay: reduceMotion.matches ? 0 : i * 45, easing: SPRING, fill: "backwards" }
    ));
  }

  function showWork(agent) {
    work.hidden = !agent;
    if (!agent) { shownAgent = null; return; }
    work.classList.toggle("is-hot", !!agent.optional);
    $("work-state").textContent = agent.optional ? "訊號出現，出動" : "正在做";
    if (shownAgent === agent.id) return;
    shownAgent = agent.id;
    $("work-no").textContent = agent.no;
    $("work-name").textContent = agent.name;
    $("work-en").textContent = agent.name_en;
    $("work-list").innerHTML = agent.did.map((d) => `<li>${zh(d)}</li>`).join("");
    $("work-files").innerHTML = agent.outputs.map((f) => `<li>${zh(f)}</li>`).join("");
    settleIn([$("work-no"), ...work.querySelectorAll(".rows li, .files li")]);
  }

  function apply(n) {
    const prev = step;
    step = Math.max(0, Math.min(LAST, Number.isFinite(n) ? n : 0));
    const agentIdx = step >= AGENT_START && step < LAST ? step - AGENT_START : -1;
    const done = step >= LAST;

    question.classList.toggle("is-in", step >= 1);
    invoke.classList.toggle("is-in", step >= 2);
    team.classList.toggle("is-in", step >= 3);

    RUN.agents.forEach((a, i) => {
      const tile = $(`tile-${a.id}`);
      const isDone = done || agentIdx > i;
      const isActive = agentIdx === i;
      tile.classList.toggle("is-done", isDone);
      tile.classList.toggle("is-active", isActive);
      tile.setAttribute("aria-current", isActive ? "step" : "false");
      tile.querySelector("[data-state]").textContent =
        isActive ? (a.optional ? "訊號出現，出動" : "正在做") : isDone ? "做完了" : a.wait;
    });

    showWork(agentIdx >= 0 ? RUN.agents[agentIdx] : null);
    report.hidden = !done;

    $("bar-step").textContent = step ? `${step}／${LAST}　${LABELS[step]}` : "";
    $("progress-bar").style.width = `${(step / LAST) * 100}%`;
    btnPause.textContent = playing ? "暫停" : "繼續";
    btnNext.disabled = done;

    if (step !== prev) {
      if (done) requestAnimationFrame(() => reveal(report, "start"));
      else if (agentIdx >= 0) requestAnimationFrame(() => reveal(work));
      else if (step === 3) reveal(team);
      else if (step <= 1) reveal(document.body, "start");
    }
  }

  function schedule() {
    clearTimer();
    if (!playing) return;
    if (step >= LAST) { playing = false; btnPause.textContent = "繼續"; return; }
    timer = setTimeout(() => { apply(step + 1); schedule(); }, holds[step + 1] || 1600);
  }

  function stop() { playing = false; clearTimer(); btnPause.textContent = "繼續"; }

  function playFrom0(delay) {
    playing = true;
    apply(0);
    clearTimer();
    timer = setTimeout(() => { apply(1); schedule(); }, delay);
  }

  btnReplay.addEventListener("click", () => playFrom0(280));
  btnPause.addEventListener("click", () => {
    if (playing) return stop();
    if (step >= LAST) return playFrom0(280);
    playing = true;
    apply(step + 1);
    schedule();
  });
  btnNext.addEventListener("click", () => { stop(); apply(step + 1); });

  /* 點角色：跳到那一步並暫停，方便上課解說 */
  tiles.addEventListener("click", (ev) => {
    const tile = ev.target.closest(".tile");
    if (!tile) return;
    const idx = RUN.agents.findIndex((a) => a.id === tile.dataset.agent);
    if (idx < 0) return;
    stop();
    apply(AGENT_START + idx);
  });

  /* 按下就回饋，不等放開 */
  document.addEventListener("pointerdown", (ev) => {
    const el = ev.target.closest(".btn:not(:disabled), .tile");
    if (!el) return;
    el.classList.add("is-pressed");
    const release = () => {
      el.classList.remove("is-pressed");
      removeEventListener("pointerup", release);
      removeEventListener("pointercancel", release);
    };
    addEventListener("pointerup", release);
    addEventListener("pointercancel", release);
  });

  /* 大標題捲到工具列下方後，工具列顯示小標題與分隔線 */
  new IntersectionObserver(([e]) => bar.classList.toggle("is-collapsed", !e.isIntersecting), {
    rootMargin: `-${bar.offsetHeight}px 0px 0px 0px`
  }).observe($("hero-title"));

  if (startStep !== null && Number.isFinite(startStep)) apply(startStep);
  else if (autoplay) playFrom0(500);
  else apply(0);

  window.DEMO = { apply, get step() { return step; }, LAST };
})();
