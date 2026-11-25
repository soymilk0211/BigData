(() => {
  const RUN = window.DEMO_RUN;
  if (!RUN) return;

  const params = new URLSearchParams(location.search);
  const startStep = params.has("step") ? Number(params.get("step")) : null;
  const autoplay = params.get("play") !== "0" && startStep === null && params.get("paused") !== "1";
  const speed = Math.max(0.4, Math.min(2, Number(params.get("speed") || 1)));
  if (params.get("record") === "1") document.body.classList.add("record");

  const $ = (id) => document.getElementById(id);
  const questionSlip = $("question-slip");
  const questionText = $("question-text");
  const skillStamp = $("skill-stamp");
  const skillName = $("skill-name");
  const agentsEl = $("agents");
  const agentsLabel = $("agents-label");
  const workEl = $("work");
  const workTitle = $("work-title");
  const workList = $("work-list");
  const workFiles = $("work-files");
  const reportEl = $("report");
  const progressBar = $("progress-bar");
  const btnReplay = $("btn-replay");
  const btnPause = $("btn-pause");
  const btnNext = $("btn-next");

  questionText.textContent = RUN.question;
  skillName.textContent = RUN.skill.name;
  $("report-title").textContent = RUN.report.title;
  $("report-conclusion").textContent = RUN.report.conclusion;
  $("report-summary").innerHTML = RUN.report.summary
    .map((s) => `<li><span class="lab">${s.label}</span><span>${s.text}</span></li>`)
    .join("");
  $("report-charts").innerHTML = RUN.report.charts
    .map((c) => `<figure><img src="${c.src}" alt="${c.alt}"><figcaption>${c.alt}</figcaption></figure>`)
    .join("");
  $("colophon").innerHTML =
    `畫面重播自 Claude Code CLI 的真實執行 <code>${RUN.source.log}</code>，` +
    `執行編號 ${RUN.source.run_id}，${RUN.source.recorded_at}，共 ${RUN.source.turns} 回合、約 ${RUN.source.duration_sec} 秒，審查 ${RUN.source.review}。` +
    `數字與結論都來自那次產出，沒有另外編造。可按「重播這次執行」再看一次。`;

  agentsEl.innerHTML = RUN.agents
    .map((a) => {
      const opt = a.optional ? " optional" : "";
      return `<article class="agent${opt}" data-agent="${a.id}" id="agent-${a.id}">
        <span class="no">${a.no}</span>
        <h3>${a.name}</h3>
        <p class="en">${a.name_en}</p>
        <p class="brief">${a.brief}</p>
        <p class="status" data-status>${a.wait}</p>
      </article>`;
    })
    .join("");

  /* 步驟：0 空白，1 提問，2 啟動 Skill，3 角色格子，4–8 各角色，9 報告 */
  const AGENT_START = 4;
  const LAST = AGENT_START + RUN.agents.length; /* 9 */
  let step = 0;
  let playing = false;
  let timer = null;

  const holds = [
    0,
    2200, /* question */
    1600, /* stamp */
    1600, /* boxes */
    4200, 4200, 4800, 4800, 3600, /* five agents, unhurried */
    0
  ].map((ms) => Math.round(ms / speed));

  function clearTimer() {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  }

  function setProgress() {
    progressBar.style.width = `${(step / LAST) * 100}%`;
  }

  function resetAgents() {
    for (const card of agentsEl.querySelectorAll(".agent")) {
      card.classList.remove("is-active", "is-done", "hot");
      const a = RUN.agents.find((x) => x.id === card.dataset.agent);
      card.querySelector("[data-status]").textContent = a ? a.wait : "";
    }
  }

  function showWork(agent, active) {
    if (!agent) {
      workEl.hidden = true;
      workEl.classList.remove("is-in");
      return;
    }
    workEl.hidden = false;
    workEl.classList.add("is-in");
    workTitle.innerHTML = `${agent.no} ${agent.name}<span>${agent.name_en}${active ? "　正在做" : "　做完了"}</span>`;
    workList.innerHTML = agent.did.map((d) => `<li>${d}</li>`).join("");
    workFiles.innerHTML = "這一步留下：" + agent.outputs.map((f) => `<code>${f}</code>`).join("、");
  }

  function apply(n) {
    step = Math.max(0, Math.min(LAST, n));
    const hasQ = step >= 1;
    const hasStamp = step >= 2;
    const hasBoxes = step >= 3;
    const agentIdx = step >= AGENT_START && step < LAST ? step - AGENT_START : -1;
    const doneReport = step >= LAST;

    questionSlip.classList.toggle("is-in", hasQ);
    skillStamp.classList.toggle("is-in", hasStamp);
    skillStamp.setAttribute("aria-hidden", hasStamp ? "false" : "true");
    agentsLabel.classList.toggle("is-in", hasBoxes);
    agentsEl.classList.toggle("is-in", hasBoxes);

    resetAgents();
    if (hasBoxes) {
      RUN.agents.forEach((a, i) => {
        const card = document.getElementById(`agent-${a.id}`);
        if (agentIdx > i || doneReport) {
          card.classList.add("is-done");
          card.querySelector("[data-status]").textContent = "做完了";
        }
        if (agentIdx === i) {
          card.classList.add("is-active");
          if (a.optional) card.classList.add("hot");
          card.querySelector("[data-status]").textContent = a.optional ? "訊號出現，出動" : "正在做";
        }
      });
    }

    if (agentIdx >= 0) showWork(RUN.agents[agentIdx], true);
    else showWork(null, false);

    reportEl.classList.toggle("is-in", doneReport);

    btnPause.textContent = playing ? "暫停" : "繼續";
    btnNext.disabled = doneReport;
    setProgress();
  }

  function schedule() {
    clearTimer();
    if (!playing) return;
    if (step >= LAST) {
      playing = false;
      btnPause.textContent = "繼續";
      return;
    }
    const wait = holds[step + 1] || 1600;
    timer = setTimeout(() => {
      apply(step + 1);
      schedule();
    }, wait);
  }

  function playFrom(n) {
    playing = true;
    apply(n);
    schedule();
  }

  btnReplay.addEventListener("click", () => {
    playFrom(0);
    timer = setTimeout(() => {
      apply(1);
      schedule();
    }, 280);
  });

  btnPause.addEventListener("click", () => {
    if (playing) {
      playing = false;
      clearTimer();
      btnPause.textContent = "繼續";
    } else if (step < LAST) {
      playing = true;
      btnPause.textContent = "暫停";
      apply(step + 1);
      schedule();
    }
  });

  btnNext.addEventListener("click", () => {
    playing = false;
    clearTimer();
    apply(step + 1);
    btnPause.textContent = "繼續";
  });

  /* 點角色格子：跳到該步並暫停，方便上課解說 */
  agentsEl.addEventListener("click", (ev) => {
    const card = ev.target.closest(".agent");
    if (!card || !agentsEl.classList.contains("is-in")) return;
    const idx = RUN.agents.findIndex((a) => a.id === card.dataset.agent);
    if (idx < 0) return;
    playing = false;
    clearTimer();
    apply(AGENT_START + idx);
    btnPause.textContent = "繼續";
  });

  if (Number.isFinite(startStep) && startStep !== null) {
    playing = false;
    apply(startStep);
  } else if (autoplay) {
    playFrom(0);
    timer = setTimeout(() => {
      apply(1);
      schedule();
    }, 500);
  } else {
    apply(0);
  }

  window.DEMO = { apply, playFrom, get step() { return step; }, LAST };
})();
