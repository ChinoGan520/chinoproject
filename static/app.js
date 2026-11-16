"use strict";
const $ = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => [...p.querySelectorAll(s)];
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const paths = {
  home: "M3 10 12 3l9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1Z",
  calendar:
    "M8 2v4m8-4v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2ZM8 14h2m4 0h2m-8 4h2",
  forum:
    "M21 11.5a8.5 8.5 0 0 1-8.5 8.5H3l2-5a8.5 8.5 0 1 1 16-3.5ZM8 10h8m-8 4h5",
  shield: "m12 2 8 3v7c0 5-8 10-8 10S4 17 4 12V5Zm-4 9 3 3 5-6",
  user: "M20 21v-2a6 6 0 0 0-6-6h-4a6 6 0 0 0-6 6v2m12-15a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
  coffee:
    "M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Zm14 1h2a3 3 0 0 1 0 6h-2M6 2v3m4-3v3m4-3v3",
  arrow: "M5 12h14m-5-5 5 5-5 5",
  chevron: "m9 5 7 7-7 7",
  bell: "M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-8 12a2 2 0 0 0 4 0",
  search: "M21 21l-5-5m2-7a7 7 0 1 1-14 0 7 7 0 0 1 14 0",
  heart:
    "M20.8 4.6a5.5 5.5 0 0 0-7.8 0l-1 1-1-1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z",
  pin: "m16 3 5 5-4 1-4 5-1 4-3-3-6 6 6-6-3-3 4-1 5-4Z",
  location:
    "M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Zm-5 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z",
  clock: "M12 7v5l4 2m6-2a10 10 0 1 1-20 0 10 10 0 0 1 20 0",
  plus: "M12 5v14m-7-7h14",
  check: "m5 12 4 4L19 6",
  close: "m6 6 12 12M6 18 18 6",
  menu: "M4 6h16M4 12h16M4 18h16",
  logout: "M9 5H5v14h4m5-14 7 7-7 7m-5-7h12",
  settings:
    "M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Zm-3-5h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1Z",
  book: "M12 5v16M3 3h5a4 4 0 0 1 4 2 4 4 0 0 1 4-2h5v16h-5a4 4 0 0 0-4 2 4 4 0 0 0-4-2H3Z",
  star: "m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z",
  people:
    "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-4M13 3a4 4 0 0 1 0 8M9 3a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z",
  edit: "m16 3 5 5-13 13H3v-5ZM14 5l5 5",
  bean: "M6 4c6-4 14 0 14 6s-8 14-14 10S0 8 6 4Zm2 0c6 5 0 11 7 14",
};
const icon = (n, cls = "") =>
  `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[n] || paths.star}"/></svg>`;
const rabbit = `<svg viewBox="0 0 56 56" fill="none" aria-hidden="true"><path d="M18 27c-8-23 1-26 6-5M32 22c5-21 15-18 6 5" stroke="currentColor" stroke-width="2.5" fill="white"/><path d="M46 36c0 11-8 16-18 16S10 47 10 36s8-17 18-17 18 6 18 17Z" fill="white" stroke="currentColor" stroke-width="2.5"/><circle cx="22" cy="34" r="1.8" fill="currentColor"/><circle cx="34" cy="34" r="1.8" fill="currentColor"/><path d="m25 40 3 2 3-2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M15 39h4m18 0h4" stroke="#e8bbc1" stroke-width="3" stroke-linecap="round"/></svg>`;
const badge = (rank, large = false) => {
  const id = Math.max(1, Math.min(19, Number(rank?.id) || 1));
  return `<span class="rank-badge ${large ? "large" : ""}" title="${esc(rank?.name || "二等兵")}"><img src="/static/art/rank-${String(id).padStart(2, "0")}.svg" alt="${esc(rank?.name || "二等兵")}咖啡軍階徽章"></span>`;
};
const avatar = (u, cls = "") =>
  `<img class="avatar ${cls}" src="/static/art/avatar-${["chino", "tippy", "coffee", "rabbit"].includes(u?.avatar) ? u.avatar : "chino"}.svg" alt="${esc(u?.username || "會員")}的頭像">`;
const fmt = (n) => Number(n || 0).toLocaleString("zh-TW");
const date = (s) => {
  let d = new Date(s);
  return Number.isNaN(+d)
    ? esc(s)
    : new Intl.DateTimeFormat("zh-TW", {
        month: "2-digit",
        day: "2-digit",
        timeZone: "Asia/Taipei",
      }).format(d);
};
const fullDate = (s) => {
  let d = new Date(s);
  return Number.isNaN(+d)
    ? esc(s)
    : new Intl.DateTimeFormat("zh-TW", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Taipei",
      }).format(d);
};
let state = {
  user: null,
  events: [],
  posts: [],
  ranks: [],
  stats: {},
  leaders: [],
  announcements: [],
};
let currentFilter = "all",
  forumFilter = "全部討論",
  adminTab = "overview";
let modalReturnFocus = null;
let pendingPromotion = null;

async function api(url, method = "GET", data) {
  const res = await fetch(url, {
    method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": state.csrf_token || "",
    },
    ...(data !== undefined ? { body: JSON.stringify(data) } : {}),
  });
  let result;
  try {
    result = await res.json();
  } catch {
    throw Error("伺服器暫時無法回應，請稍後再試。");
  }
  if (!res.ok)
    throw Error(result.error || result.message || "操作未完成，請重試。");
  if (result.csrf_token) state.csrf_token = result.csrf_token;
  return result;
}
async function sync() {
  const before = state.user;
  state = await api("/api/bootstrap");
  if (
    before &&
    state.user?.id === before.id &&
    state.user.rank?.id > before.rank?.id
  )
    pendingPromotion = state.user.rank;
  renderShell();
}
function toast(message, error = false) {
  const el = document.createElement("div");
  el.className = "toast" + (error ? " error" : "");
  el.textContent = message;
  $("#toast-region").append(el);
  setTimeout(() => el.remove(), 4800);
}
function modal(html, wide = false) {
  modalReturnFocus = document.activeElement;
  $("#modal").className = "modal" + (wide ? " wide" : "");
  $("#modal").innerHTML =
    `<button class="modal-close icon-button" aria-label="關閉視窗" data-close>${icon("close")}</button>${html}`;
  $("#modal-backdrop").hidden = false;
  document.body.classList.add("modal-open");
  ($("#modal input") || $("#modal")).focus();
}
function closeModal() {
  $("#modal-backdrop").hidden = true;
  document.body.classList.remove("modal-open");
  modalReturnFocus?.focus();
}
function requireUser() {
  if (state.user) return true;
  showAuth();
  return false;
}
function go(path) {
  history.pushState({}, "", path);
  currentFilter = "all";
  forumFilter = "全部討論";
  render();
  window.scrollTo({ top: 0, behavior: "instant" });
  $("#sidebar").classList.remove("open");
  $("#menu-toggle").setAttribute("aria-expanded", "false");
}
function routeTitle() {
  let p = location.pathname;
  return p.startsWith("/events")
    ? "應援活動"
    : p.startsWith("/forum")
      ? "親衛隊論壇"
      : p === "/ranks"
        ? "軍階榮譽殿堂"
        : p === "/profile"
          ? "我的軍籍"
          : p === "/admin"
            ? "總司令部"
            : "應援總覽";
}
function renderShell() {
  const links = [
    ["/", "home", "應援總覽"],
    ["/events", "calendar", "應援活動"],
    ["/forum", "forum", "親衛隊論壇"],
    ["/ranks", "shield", "軍階榮譽殿堂"],
    ["/profile", "user", "我的軍籍"],
  ];
  if (state.user?.role === "admin")
    links.push(["/admin", "settings", "總司令部"]);
  $("#navigation").innerHTML = links
    .map(
      ([url, i, t]) =>
        `<a href="${url}" class="nav-item ${location.pathname === url || (url !== "/" && location.pathname.startsWith(url + "/")) ? "active" : ""}">${icon(i)}<span>${t}</span>${url === "/events" ? `<span class="nav-count">${state.events.filter((e) => e.status !== "closed").length}</span>` : ""}</a>`,
    )
    .join("");
  $("#header-user").innerHTML = state.user
    ? `<button class="user-trigger" data-go="/profile">${avatar(state.user)}<span>${esc(state.user.username)}<small>${esc(state.user.rank?.name)}</small></span>${icon("chevron")}</button>`
    : `<button class="button small primary" data-auth>登入 / 加入我們</button>`;
  $("#breadcrumb-current").textContent = routeTitle();
}
function sectionHead(kicker, title, href, label = "查看全部") {
  return `<div class="section-head"><div><span class="eyebrow">${kicker}</span><h2>${title}</h2></div>${href ? `<a class="text-link" href="${href}">${label} ${icon("arrow")}</a>` : ""}</div>`;
}
function pageIntro(kicker, title, description, action = "") {
  return `<div class="page-intro"><div><span class="eyebrow">${kicker}</span><h1>${title}</h1><p>${description}</p></div>${action}</div>`;
}
function eventState(e) {
  if (e.status === "closed" || new Date(e.end_time) < new Date())
    return ["ended", "已結束"];
  if (new Date(e.start_time) <= new Date()) return ["live", "進行中"];
  return ["soon", "即將開始"];
}
function eventArt(e) {
  const v = e.art || "";
  return /birthday|cafe|drawing/.test(v)
    ? v.match(/birthday|cafe|drawing/)[0]
    : /生日/.test(e.title)
      ? "birthday"
      : /繪|二創/.test(e.title)
        ? "drawing"
        : "cafe";
}
function eventCard(e) {
  const [status, label] = eventState(e);
  return `<a class="event-card" href="/events/${e.id}"><div class="event-image ${eventArt(e)}"><img src="/static/art/${eventArt(e)}.svg" alt="${esc(e.event_type)}主題插畫"><span class="pill ${status}"><i></i>${label}</span>${e.registered ? '<span class="registered-label">已報名</span>' : ""}</div><div class="event-card-body"><div class="event-meta"><span>${esc(e.event_type)}</span><span>${icon("bean")} +${fmt(e.reward_exp)} EXP</span></div><h3>${esc(e.title)}</h3><p class="event-description">${esc(e.description).slice(0, 70)}</p><div class="event-bottom"><span>${icon("calendar")}${date(e.start_time)}</span><span>${icon("location")}${esc(e.location || "線上活動")}</span><span class="card-arrow">${icon("arrow")}</span></div></div></a>`;
}
function postRow(p) {
  return `<a href="/forum/${p.id}" class="post-row"><span class="post-category ${p.is_announcement ? "announcement" : ""}">${esc(p.category)}</span><div class="post-main"><h3>${p.is_pinned ? icon("pin") : ""}${esc(p.title)}${p.locked ? "<small>已鎖定</small>" : ""}</h3><div class="post-byline">${esc(p.author)}<span>·</span>${date(p.created_at)}</div></div><span class="post-counter">${icon("forum")}${fmt(p.comment_count)}</span><span class="post-counter">${icon("heart")}${fmt(p.likes)}</span>${icon("chevron", "post-chevron")}</a>`;
}
function dailyCard() {
  const u = state.user;
  return `<section class="card daily-card"><div class="daily-top"><span class="eyebrow">DAILY MOMENT</span><span class="tiny-label">每日應援</span></div><div class="daily-illustration">${rabbit}<span class="spark s1">✦</span><span class="spark s2">✧</span><span class="daily-bean">${icon("bean")}</span></div><h3>${u?.checked_in ? "今天的心意，收到了。" : "今天，也來一杯嗎？"}</h3><p>${u ? "每日簽到，累積一點點喜歡。" : "登入簽到，開啟你的應援日常。"}</p><button class="button primary full" data-checkin ${u?.checked_in ? "disabled" : ""}>${icon(u?.checked_in ? "check" : "coffee")}${u?.checked_in ? "今日已簽到" : "每日簽到"}<span>+20 EXP</span></button><small>每一天的陪伴，都值得被記錄。</small></section>`;
}
function memberCard() {
  const u = state.user;
  if (!u)
    return `<section class="card member-card"><div class="mini-section-title">${icon("shield")} 你的應援，值得一枚徽章</div><div class="guest-badge">${badge(null, true)}</div><h3>從一顆咖啡豆開始</h3><p>加入親衛隊，解鎖專屬軍籍<br>與 19 階的應援旅程。</p><button class="button outline full" data-auth="register">領取我的軍籍 ${icon("arrow")}</button></section>`;
  return `<section class="card member-card"><div class="mini-section-title">${icon("shield")} 我的軍籍 <a href="/profile">${icon("arrow")}</a></div><div class="member-rank">${badge(u.rank, true)}<div><span class="tiny-label">${esc(u.rank?.title)}</span><h3>${esc(u.rank?.name)}</h3><span>${fmt(u.exp)} <small>EXP</small></span></div></div><div class="progress-caption"><span>晉升進度</span><b>${u.next_rank ? esc(u.next_rank.name) : "最高榮譽"}</b></div><div class="progress-track"><div style="width:${Math.min(100, Math.max(0, u.progress || 0))}%"></div></div><p class="progress-hint">${u.next_rank ? `再收集 <b>${fmt(u.next_rank.min_exp - u.exp)}</b> 顆咖啡豆，即可晉升` : "謝謝你一直以來的陪伴。"}</p></section>`;
}
function leaderboard() {
  return `<section class="card leaderboard"><div class="mini-section-title">${icon("star")} 本站應援之星 <span class="tiny-label">TOP 3</span></div>${
    state.leaders.length
      ? state.leaders
          .slice(0, 3)
          .map(
            (u, i) =>
              `<div class="leader-row"><span class="leader-number n${i}">0${i + 1}</span>${avatar(u)}<div><b>${esc(u.username)}</b><small>${esc(u.rank?.name || u.army_rank_name || "應援隊員")}</small></div><span>${fmt(u.exp)}<small>EXP</small></span></div>`,
          )
          .join("")
      : '<p class="empty-small">下一顆應援之星，也許就是你。</p>'
  }<div class="leader-note">每一份心意，都是閃閃發亮的存在。</div></section>`;
}
function home() {
  const ann =
    state.announcements[0] || state.posts.find((p) => p.is_announcement);
  const open = state.events
    .filter((e) => eventState(e)[0] !== "ended")
    .slice(0, 3);
  return `<div class="home-welcome"><div><span class="eyebrow">A LITTLE COFFEE, A LOT OF LOVE</span><h1>${state.user ? `歡迎回來，${esc(state.user.username)}。` : "今天，也為智乃應援。"} <span class="title-spark">✧</span></h1><p>在 Rabbit House，讓每一份喜歡都有溫暖的歸屬。</p></div><div class="today-label">${icon("calendar")} <span>${new Intl.DateTimeFormat("zh-TW", { month: "long", day: "numeric", weekday: "long", timeZone: "Asia/Taipei" }).format(new Date())}</span></div></div><div class="dashboard-grid"><div class="dashboard-main"><section class="hero"><div class="hero-content"><div class="hero-kicker"><span></span> CHINO KAFŪ FAN COMMUNITY</div><h2>把喜歡，釀成<br>每一天的陪伴<span>。</span></h2><p>歡迎來到智乃親衛隊。<br>一杯咖啡的時間，和同好收藏美好日常。</p><a class="button dark" href="/events">探索應援活動 ${icon("arrow")}</a><div class="hero-footnote"><span>♡</span> OUR STORY BEGINS WITH YOU</div></div><div class="hero-art"><img src="/static/art/hero.svg" alt="粉藍長髮的智乃與白色安哥拉兔在溫暖的 Rabbit House 咖啡廳"></div><span class="hero-stamp">Rabbit House<br><b>WITH LOVE</b><span>✧</span></span></section>${ann ? `<a href="/forum/${ann.id}" class="announcement-strip"><span class="broadcast-icon">${icon("bell")}</span><span class="broadcast-label">司令部廣播</span><span class="broadcast-title">${esc(ann.title)}</span><span class="broadcast-date">${date(ann.created_at)}</span>${icon("chevron")}</a>` : ""}<div class="stat-grid"><div>${icon("people")}<span><small>親衛隊隊員</small><b>${fmt(state.stats.members)}<em> 位</em></b></span></div><div>${icon("calendar")}<span><small>應援活動</small><b>${fmt(state.stats.events)}<em> 場</em></b></span></div><div>${icon("forum")}<span><small>日常的交流</small><b>${fmt(state.stats.posts)}<em> 篇</em></b></span></div><div>${icon("bean")}<span><small>累積應援能量</small><b>${fmt(state.stats.total_exp)}<em> EXP</em></b></span></div></div>${sectionHead("LET’S MAKE MEMORIES", "一起創造，新的回憶", "/events", "所有活動")}<div class="event-grid home-events">${open.length ? open.map(eventCard).join("") : '<div class="empty-state">新的應援活動正在準備中。</div>'}</div><section class="forum-preview">${sectionHead("CONVERSATIONS OVER COFFEE", "咖啡桌邊的悄悄話", "/forum", "走進論壇")}<div class="card post-list">${
    state.posts
      .filter((p) => !p.is_announcement)
      .slice(0, 3)
      .map(postRow)
      .join("") || '<p class="empty-state">來分享第一個故事吧。</p>'
  }</div></section></div><aside class="dashboard-aside">${dailyCard()}${memberCard()}${leaderboard()}<div class="birthday-note"><span>12.04</span><div>Happy Birthday, Chino.<small>把最溫柔的祝福，留給妳。</small></div>${icon("heart")}</div></aside></div>`;
}
function eventsPage() {
  let es = state.events.filter(
    (e) => currentFilter === "all" || eventState(e)[0] === currentFilter,
  );
  return `${pageIntro("CHINO EVENTS", "把日常，變成值得紀念的日子。", "線上相聚、咖啡巡禮、生日應援。下一段回憶，一起參與。")}<div class="toolbar"><div class="tabs" role="tablist" aria-label="活動狀態">${[
    ["all", "全部活動"],
    ["live", "進行中"],
    ["soon", "即將開始"],
    ["ended", "已結束"],
  ]
    .map(
      ([key, t]) =>
        `<button role="tab" aria-selected="${currentFilter === key}" class="tab ${currentFilter === key ? "active" : ""}" data-filter="${key}">${t}<span>${state.events.filter((e) => key === "all" || eventState(e)[0] === key).length}</span></button>`,
    )
    .join(
      "",
    )}</div><span class="muted small-text">每一次參與，都是一份心意。</span></div><div class="event-grid full-events">${es.length ? es.map(eventCard).join("") : '<div class="empty-state card">這裡還沒有活動，先去其他分類看看吧。</div>'}</div>`;
}
async function eventDetail(id) {
  try {
    const data = await api(`/api/events/${id}`);
    const e = data.event || data;
    const [s, label] = eventState(e);
    $("#main").innerHTML =
      `<a class="back-link" href="/events">← 返回應援活動</a><div class="detail-grid"><article class="card event-detail"><div class="detail-cover ${eventArt(e)}"><img src="/static/art/${eventArt(e)}.svg" alt="${esc(e.event_type)}插畫"><span class="pill ${s}">${label}</span></div><div class="detail-content"><span class="eyebrow">${esc(e.event_type)}</span><h1>${esc(e.title)}</h1><div class="detail-meta"><span>${icon("calendar")}${fullDate(e.start_time)}</span><span>${icon("location")}${esc(e.location)}</span></div><h2>關於這次相聚</h2><div class="prose">${esc(e.description)}</div><div class="info-box">${icon("coffee")} 完成活動後，由司令部確認參與紀錄並發放咖啡豆。</div></div></article><aside><section class="card registration-card"><span class="eyebrow">YOUR NEXT MEMORY</span><h2>為喜歡，留一個位置。</h2><div class="registration-fact"><span>完成獎勵</span><b class="blue">+${fmt(e.reward_exp)} EXP</b></div><div class="registration-fact"><span>參與條件</span><b>${e.min_exp ? `${fmt(e.min_exp)} EXP 以上` : "所有親衛隊隊員"}</b></div><div class="registration-fact"><span>報名人數</span><b>${fmt(e.registered_count)} / ${e.capacity || "不限"}</b></div><div class="registration-fact"><span>活動截止</span><b>${date(e.end_time)}</b></div>${e.registration_status === "attended" ? '<div class="info-box">已完成參與，獎勵已發放。</div>' : e.registered ? `<div class="joined-box">${icon("check")} 你已成功報名</div><button class="button outline full" data-event-cancel="${e.id}">取消報名</button>` : `<button class="button primary full" data-event-register="${e.id}" ${s === "ended" ? "disabled" : ""}>${icon("heart")}${s === "ended" ? "活動已結束" : "我要參加這次應援"}</button>`}<p class="muted small-text">${state.user ? "報名即代表同意友善參與社群活動。" : "請先登入並完成 Email 驗證後報名。"}</p></section><div class="side-quote">“ 只要有你們在，<br>每天都是特別的一天。 ”<small>— Rabbit House</small></div></aside></div>`;
  } catch (e) {
    $("#main").innerHTML = errorPage(e.message);
  }
}
function forumPage() {
  const cats = [
    "全部討論",
    "司令部廣播",
    "聖地巡禮",
    "周邊開箱",
    "動畫心得",
    "日常閒聊",
    "二創分享",
  ];
  const ps = state.posts.filter(
    (p) =>
      forumFilter === "全部討論" ||
      (forumFilter === "司令部廣播"
        ? p.is_announcement
        : p.category === forumFilter),
  );
  return `${pageIntro("OUR LITTLE CONVERSATIONS", "找張椅子，聊聊你的喜歡。", "從一段動畫心得，到一杯咖啡的日常。這裡，總有懂你的人。", `<button class="button primary" data-new-post>${icon("plus")}分享新話題</button>`)}<div class="forum-layout"><div><div class="toolbar forum-tabs"><div class="tabs">${cats.map((c) => `<button class="tab ${forumFilter === c ? "active" : ""}" data-forum-filter="${c}">${c}</button>`).join("")}</div></div><div class="card post-list full-post-list">${ps.length ? ps.map(postRow).join("") : '<div class="empty-state">還沒有話題。來分享你的第一個故事吧。</div>'}</div></div><aside><section class="card community-guidelines"><div class="guideline-icon">${icon("coffee")}</div><h3>溫柔，是我們的默契。</h3><p>尊重每一份喜歡，善待每一位同好。</p><ul><li>分享作品時，請附上原作者與來源。</li><li>避免劇透，或在標題清楚標示。</li><li>一起維護友善、沒有爭吵的空間。</li></ul><span class="tiny-label">MAKE YOURSELF AT HOME</span></section></aside></div>`;
}
async function postDetail(id) {
  try {
    const data = await api(`/api/posts/${id}`);
    const p = data.post || data;
    const comments = data.comments || p.comments || [];
    $("#main").innerHTML =
      `<a class="back-link" href="/forum">← 返回親衛隊論壇</a><article class="card post-detail"><div class="post-detail-top"><span class="post-category ${p.is_announcement ? "announcement" : ""}">${esc(p.category)}</span>${p.is_pinned ? '<span class="tiny-label">置頂話題</span>' : ""}${p.locked ? '<span class="tiny-label">討論已鎖定</span>' : ""}</div><h1>${esc(p.title)}</h1><div class="post-author"><span class="author-initial">${esc(p.author?.[0] || "R")}</span><div><b>${esc(p.author)}</b><small>${fullDate(p.created_at)} · ${esc(typeof p.author_rank === "object" ? p.author_rank.name : p.author_rank || "親衛隊隊員")}</small></div></div><div class="prose post-content">${esc(p.content)}</div><div class="post-actions"><button class="button ${p.liked ? "primary" : "outline"}" data-like="${p.id}">${icon("heart")}${p.liked ? "已送出喜歡" : "喜歡這個話題"} <span>${fmt(p.likes)}</span></button><span class="muted">${comments.length} 則回覆</span></div></article><section class="card comments-section"><h2>咖啡桌邊的回覆 <span>${comments.length}</span></h2>${comments.map((c) => `<div class="comment"><span class="author-initial">${esc(c.author?.[0] || "R")}</span><div><div><b>${esc(c.author)}</b><small>${fullDate(c.created_at)}</small></div><p>${esc(c.content)}</p></div></div>`).join("") || '<p class="empty-small">第一句溫暖的回應，就從你開始。</p>'}${p.locked ? '<div class="info-box">這個話題已鎖定，暫時無法新增回覆。</div>' : state.user ? `<form id="comment-form" data-post-id="${p.id}"><label for="comment-content">留下一句溫柔的話</label><textarea id="comment-content" name="content" required maxlength="2000" rows="4" placeholder="分享你的想法…"></textarea><button class="button primary" type="submit">送出回覆 ${icon("arrow")}</button></form>` : '<button class="button outline" data-auth>登入後加入討論</button>'}</section>`;
  } catch (e) {
    $("#main").innerHTML = errorPage(e.message);
  }
}
function ranksPage() {
  const categories = [...new Set(state.ranks.map((r) => r.category))];
  return `${pageIntro("A JOURNEY OF DEVOTION", "每一份陪伴，都有它的榮耀。", "以咖啡豆記錄你的應援足跡。從咖啡廳見習生，到親衛隊總司令。")}<div class="rank-intro card"><div>${badge(state.user?.rank, true)}<div><span class="eyebrow">YOUR JOURNEY</span><h2>${state.user ? `你目前是「${esc(state.user.rank?.name)}」` : "你的旅程，從這裡開始。"}</h2><p>${state.user ? `累積 ${fmt(state.user.exp)} EXP · ${esc(state.user.rank?.title)}` : "註冊即成為二等兵，領取屬於你的第一枚徽章。"}</p></div></div><button class="button primary" ${state.user ? 'data-go="/profile"' : 'data-auth="register"'}>${state.user ? "查看我的軍籍" : "加入親衛隊"}${icon("arrow")}</button></div><div class="exp-guide"><div>${icon("coffee")}<b>每日簽到</b><span>+20 EXP / 日</span></div><div>${icon("calendar")}<b>參與活動</b><span>依活動完成獎勵</span></div><div>${icon("forum")}<b>分享與互動</b><span>發文 +5 · 回覆 +2 · 獲讚 +1</span></div></div>${categories
    .map(
      (c, i) =>
        `<section class="rank-section"><div class="section-head"><h2><span class="chapter-number">0${i + 1}</span>${esc(c)}</h2><span class="tiny-label">${i === categories.length - 1 ? "LOYALTY & HONOR" : "EVERY LITTLE MOMENT COUNTS"}</span></div><div class="rank-grid">${state.ranks
          .filter((r) => r.category === c)
          .map(
            (r) =>
              `<article class="card rank-card ${state.user?.rank?.id === r.id ? "current" : ""}">${badge(r, true)}<div><span class="tiny-label">RANK ${String(r.id).padStart(2, "0")}</span><h3>${esc(r.name)}</h3><p>${esc(r.title)}</p><b>${r.name === "一級上將" ? "管理員特任榮譽" : `${fmt(r.min_exp)} EXP`}</b></div>${state.user?.rank?.id === r.id ? '<span class="current-tag">目前軍階</span>' : ""}</article>`,
          )
          .join("")}</div></section>`,
    )
    .join(
      "",
    )}<div class="info-box rank-disclaimer">${icon("book")} 本站為非官方粉絲應援社群。軍階名稱參考中華民國陸軍制度，徽章為原創咖啡主題設計，EXP 門檻為本站自訂。一級上將為管理員特任榮譽。</div>`;
}
function profilePage() {
  const u = state.user;
  if (!u) return authLanding();
  return `${pageIntro("MY SERVICE RECORD", "每一天的喜歡，都在這裡。", "這是你的專屬軍籍，收藏你在 Rabbit House 的每一步。", `<button class="button outline" data-logout>${icon("logout")}登出帳號</button>`)}<div class="profile-layout"><section class="card profile-card"><div class="profile-cover"><span>RABBIT HOUSE</span>${rabbit}</div><div class="profile-avatar">${avatar(u)}</div><div class="profile-info"><span class="pill soon">${u.role === "admin" ? "總司令部" : "智乃親衛隊隊員"}</span><h1>${esc(u.username)}</h1><p>${esc(u.email)}</p><span class="tiny-label">入伍日期 ${date(u.created_at)}</span>${!u.verified ? '<div class="info-box">請先開啟註冊信中的連結，完成 Email 驗證。</div>' : ""}<button class="button outline full" data-edit-profile>${icon("edit")}編輯軍籍資料</button></div></section><div>${memberCard()}<section class="card profile-events"><div class="mini-section-title">${icon("calendar")} 我的應援活動</div>${
    state.events
      .filter((e) => e.registered)
      .map(
        (e) =>
          `<a class="my-event" href="/events/${e.id}"><img src="/static/art/${eventArt(e)}.svg" alt="活動插畫"><div><b>${esc(e.title)}</b><small>${date(e.start_time)} · ${e.registration_status === "attended" ? "已完成參與" : "已報名"}</small></div>${icon("chevron")}</a>`,
      )
      .join("") ||
    '<div class="empty-small">你的下一段回憶，正在等你。<a href="/events" class="text-link">探索活動 →</a></div>'
  }</section>${dailyCard()}</div></div>`;
}
function authLanding() {
  return `<div class="auth-landing card"><div class="auth-mascot">${rabbit}</div><span class="eyebrow">WELCOME TO OUR LITTLE WORLD</span><h1>這裡，為你留了一個位置。</h1><p>加入智乃親衛隊，開啟屬於你的咖啡廳日常。</p><button class="button primary" data-auth>登入 / 加入我們 ${icon("arrow")}</button></div>`;
}
function showAuth(mode = "login") {
  const reg = mode === "register";
  modal(
    `<div class="auth-logo">${rabbit}</div><span class="eyebrow">RABBIT HOUSE · FAN CLUB</span><h2 id="modal-title">${reg ? "歡迎加入，新的親衛隊員。" : "歡迎回來，咖啡已經準備好了。"}</h2><p class="modal-subtitle">${reg ? "讓每一份喜歡，都有溫暖的歸屬。" : "登入，繼續收藏今天的小小美好。"}</p><form id="auth-form" data-mode="${reg ? "register" : "login"}"><label for="auth-username">${reg ? "暱稱 / 帳號" : "帳號"}<input id="auth-username" name="username" required minlength="${reg ? 2 : 1}" maxlength="24" autocomplete="username" placeholder="你的咖啡廳暱稱"></label>${reg ? '<label for="auth-email">Email<input id="auth-email" type="email" name="email" required autocomplete="email" placeholder="you@example.com"></label>' : ""}<label for="auth-password">密碼<input id="auth-password" type="password" name="password" required minlength="${reg ? 8 : 1}" maxlength="128" autocomplete="${reg ? "new-password" : "current-password"}" placeholder="${reg ? "至少 8 個字元" : "輸入你的密碼"}"></label>${reg ? "" : `<label class="checkbox-label"><input type="checkbox" name="remember">記住我的登入狀態</label>`}<div class="form-error" role="alert"></div><button class="button primary full" type="submit">${reg ? "建立我的軍籍" : "登入 Rabbit House"}${icon("arrow")}</button></form><p class="auth-switch">${reg ? "已經是親衛隊隊員？" : "還沒加入我們？"}<button data-auth="${reg ? "login" : "register"}">${reg ? "登入帳號" : "立即註冊"}</button></p>${state.demo_mode ? '<div class="demo-hint"><b>預覽體驗帳號</b><button data-demo="member">一般會員 chino</button><button data-demo="admin">管理員 commander</button><small>僅限開發預覽；測試資料與真實會員分開。</small></div>' : ""}`,
  );
}
function newPost() {
  if (!requireUser()) return;
  modal(
    `<span class="eyebrow">SHARE A LITTLE HAPPINESS</span><h2 id="modal-title">今天，想聊些什麼？</h2><form id="new-post-form"><label for="post-category">話題分類<select id="post-category" name="category">${["日常閒聊", "動畫心得", "周邊開箱", "聖地巡禮", "二創分享"].map((x) => `<option>${esc(x)}</option>`).join("")}</select></label><label for="post-title">話題標題<input id="post-title" name="title" required maxlength="120" placeholder="用一句話，開啟今天的對話"></label><label for="post-content">分享內容<textarea id="post-content" name="content" required maxlength="10000" rows="7" placeholder="寫下你的故事…"></textarea></label><div class="form-error" role="alert"></div><button class="button primary" type="submit">發布話題 ${icon("arrow")}</button></form>`,
    true,
  );
}
function editProfile() {
  modal(
    `<h2 id="modal-title">編輯你的軍籍</h2><form id="profile-form"><label for="profile-name">暱稱<input id="profile-name" name="username" value="${esc(state.user.username)}" required minlength="2" maxlength="24"></label><fieldset class="avatar-picker"><legend>選擇頭像</legend>${["chino", "tippy", "coffee", "rabbit"].map((a, i) => `<label><input type="radio" name="avatar" value="${a}" ${a === state.user.avatar ? "checked" : ""}>${avatar({ avatar: a, username: ["智乃", "提比", "咖啡", "兔兔"][i] })}<span>${["智乃", "提比", "咖啡", "兔兔"][i]}</span></label>`).join("")}</fieldset><div class="form-error" role="alert"></div><button class="button primary full">儲存軍籍 ${icon("check")}</button></form>`,
  );
}
function errorPage(msg) {
  return `<div class="empty-state card"><h2>這杯咖啡還沒準備好。</h2><p>${esc(msg)}</p><a href="/" class="button outline">回到總覽</a></div>`;
}
async function render() {
  renderShell();
  const p = location.pathname.replace(/\/$/, "") || "/";
  const main = $("#main");
  if (/^\/events\/\d+$/.test(p)) {
    main.innerHTML = '<div class="loading-state">正在準備活動詳情…</div>';
    await eventDetail(p.split("/")[2]);
  } else if (/^\/forum\/\d+$/.test(p)) {
    main.innerHTML = '<div class="loading-state">正在閱讀話題…</div>';
    await postDetail(p.split("/")[2]);
  } else if (p === "/admin") {
    await adminPage();
  } else {
    main.innerHTML =
      p === "/"
        ? home()
        : p === "/events"
          ? eventsPage()
          : p === "/forum"
            ? forumPage()
            : p === "/ranks"
              ? ranksPage()
              : p === "/profile"
                ? profilePage()
                : p === "/login" || p === "/register"
                  ? authLanding()
                  : errorPage("找不到這個頁面。");
    if (p === "/login" || p === "/register")
      showAuth(p === "/register" ? "register" : "login");
  }
  document.title = `${routeTitle()} · Rabbit House 智乃親衛隊`;
  if (pendingPromotion && $("#modal-backdrop").hidden) {
    const rank = pendingPromotion;
    pendingPromotion = null;
    showPromotion(rank);
  }
}

let adminData = null;
async function adminPage() {
  if (state.user?.role !== "admin") {
    $("#main").innerHTML = errorPage("這裡是總司令部，僅限管理員進入。");
    return;
  }
  try {
    adminData = await api("/api/admin");
    $("#main").innerHTML =
      `${pageIntro("COMMAND HEADQUARTERS", "總司令部，今日執勤中。", "管理每一次相聚，照顧社群裡的每一份心意。", `<button class="button primary" data-admin-new-event>${icon("plus")}建立新活動</button>`)}<div class="tabs admin-tabs">${[
        ["overview", "總覽"],
        ["events", "活動與積分"],
        ["users", "人事命令"],
        ["posts", "論壇與廣播"],
        ["logs", "操作紀錄"],
      ]
        .map(
          ([v, t]) =>
            `<button class="tab ${adminTab === v ? "active" : ""}" data-admin-tab="${v}">${t}</button>`,
        )
        .join("")}</div><div id="admin-panel">${adminPanel()}</div>`;
  } catch (e) {
    $("#main").innerHTML = errorPage(e.message);
  }
}
function adminPanel() {
  const d = adminData;
  if (adminTab === "overview")
    return `<div class="admin-summary"><div class="card">${icon("people")}<small>社群會員</small><b>${d.users.length}</b></div><div class="card">${icon("calendar")}<small>應援活動</small><b>${d.events.length}</b></div><div class="card">${icon("forum")}<small>論壇話題</small><b>${d.posts.length}</b></div></div><section class="card admin-welcome"><span class="eyebrow">TODAY’S MISSION</span><h2>讓每一份應援，得到溫柔的回應。</h2><p>在「活動與積分」核對出席並發放獎勵；在「人事命令」管理會員；在「論壇與廣播」發布社群公告。所有管理操作皆會留下紀錄。</p></section>`;
  if (adminTab === "events")
    return `<div class="admin-event-list">${d.events
      .map(
        (e) =>
          `<section class="card admin-event"><div class="admin-row-title"><div><span class="tiny-label">${esc(e.event_type)}</span><h3>${esc(e.title)}</h3><p>${date(e.start_time)} · +${fmt(e.reward_exp)} EXP · ${e.status === "closed" ? "已下架" : "開放中"}</p></div><div class="inline-actions"><button class="button small outline" data-admin-edit-event="${e.id}">${icon("edit")}編輯</button><button class="button small outline danger" data-admin-close-event="${e.id}">下架</button></div></div><form class="award-form" data-event-id="${e.id}"><div class="registration-list">${
            d.registrations
              .filter((r) => r.event_id === e.id)
              .map(
                (r) =>
                  `<label class="registration-entry"><input type="checkbox" name="user_ids" value="${r.user_id}" ${r.status === "attended" ? "disabled" : ""}><span>${esc(r.username || d.users.find((u) => u.id === r.user_id)?.username || `隊員 #${r.user_id}`)}</span><small>${r.status === "attended" ? "已發放獎勵" : "待確認出席"}</small></label>`,
              )
              .join("") || '<p class="empty-small">目前還沒有報名紀錄。</p>'
          }</div><div class="form-error" role="alert"></div><button class="button small primary" type="submit">${icon("check")}確認出席並發放積分</button></form></section>`,
      )
      .join("")}</div>`;
  if (adminTab === "users")
    return `<div class="admin-search"><label for="member-search">${icon("search")}<input id="member-search" type="search" placeholder="搜尋會員帳號或 Email"></label></div><div class="card table-scroll"><table><thead><tr><th>隊員</th><th>權限</th><th>咖啡豆</th><th>狀態</th><th>人事命令</th></tr></thead><tbody id="member-rows">${userRows(d.users)}</tbody></table></div>`;
  if (adminTab === "posts")
    return `<button class="button primary broadcast-create" data-new-announcement>${icon("bell")}發布司令部廣播</button><div class="card table-scroll"><table><thead><tr><th>話題</th><th>狀態</th><th>管理</th></tr></thead><tbody>${d.posts.map((p) => `<tr><td><a href="/forum/${p.id}">${esc(p.title)}</a><small>${esc(p.author || "")} · ${esc(p.category)}</small></td><td>${p.is_pinned ? "置頂 " : ""}${p.is_announcement ? "廣播 " : ""}${p.locked ? "已鎖定" : "討論中"}</td><td><div class="inline-actions"><button class="button tiny outline" data-pin-post="${p.id}">${p.is_pinned ? "取消置頂" : "置頂"}</button><button class="button tiny outline" data-lock-post="${p.id}">${p.locked ? "解鎖" : "鎖定"}</button><button class="button tiny outline danger" data-delete-post="${p.id}">刪除</button></div></td></tr>`).join("")}</tbody></table></div>`;
  return `<div class="card table-scroll"><table><thead><tr><th>時間</th><th>執行者</th><th>操作</th><th>詳細紀錄</th></tr></thead><tbody>${(d.audit_logs || []).map((l) => `<tr><td>${fullDate(l.created_at)}</td><td>${esc(l.admin_name || l.actor || l.username || l.admin_id || l.actor_id)}</td><td>${esc(l.action)}</td><td>${esc(l.details)}</td></tr>`).join("") || '<tr><td colspan="4">目前沒有管理操作紀錄。</td></tr>'}</tbody></table></div>`;
}
function userRows(users) {
  return users
    .map(
      (u) =>
        `<tr><td><b>${esc(u.username)}</b><small>${esc(u.email)}</small></td><td>${u.role === "admin" ? "管理員" : "一般會員"}</td><td>${fmt(u.exp)} EXP</td><td><span class="pill ${u.banned ? "ended" : "live"}">${u.banned ? "已封鎖" : u.verified ? "已驗證" : "未驗證"}</span></td><td><button class="button small outline" data-edit-member="${u.id}">管理 ${icon("chevron")}</button></td></tr>`,
    )
    .join("");
}
function adminEventForm(id) {
  const e = adminData.events.find((e) => e.id === id) || {};
  const local = (s) => {
    if (!s) return "";
    const d = new Date(s);
    return new Date(d.getTime() + 8 * 3600000).toISOString().slice(0, 16);
  };
  modal(
    `<span class="eyebrow">PLAN OUR NEXT MEMORY</span><h2 id="modal-title">${id ? "編輯應援活動" : "建立新的應援活動"}</h2><form id="admin-event-form" data-id="${id || ""}"><label>活動名稱<input name="title" required maxlength="120" value="${esc(e.title)}"></label><div class="form-grid"><label>活動類型<select name="event_type">${[...new Set([e.event_type, "生日祭", "咖啡聚會", "二創徵集", "知識問答", "生日應援", "咖啡巡禮", "二創企劃", "線上活動"].filter(Boolean))].map((x) => `<option ${e.event_type === x ? "selected" : ""}>${esc(x)}</option>`).join("")}</select></label><label>活動插畫<select name="art">${[
      ["birthday", "生日蛋糕"],
      ["cafe", "咖啡相聚"],
      ["drawing", "二創繪圖"],
    ]
      .map(
        ([v, t]) =>
          `<option value="${v}" ${eventArt(e) === v ? "selected" : ""}>${t}</option>`,
      )
      .join(
        "",
      )}</select></label><label>開始時間（臺灣時間）<input type="datetime-local" name="start_time" required value="${local(e.start_time)}"></label><label>結束時間（臺灣時間）<input type="datetime-local" name="end_time" required value="${local(e.end_time)}"></label><label>完成獎勵 EXP<input type="number" min="0" max="10000" name="reward_exp" required value="${e.reward_exp ?? 100}"></label><label>最低參與 EXP<input type="number" min="0" max="1000000" name="min_exp" required value="${e.min_exp ?? 0}"></label><label>人數上限<input type="number" min="1" max="100000" name="capacity" required value="${e.capacity ?? 100}"></label><label>活動狀態<select name="status"><option value="open">開放</option><option value="closed" ${e.status === "closed" ? "selected" : ""}>下架</option></select></label></div><label>地點 / 活動網址<input name="location" required maxlength="200" value="${esc(e.location)}"></label><label>活動介紹<textarea name="description" rows="5" required maxlength="10000">${esc(e.description)}</textarea></label><div class="form-error" role="alert"></div><button class="button primary">儲存活動 ${icon("check")}</button></form>`,
    true,
  );
}
function editMember(id) {
  const u = adminData.users.find((u) => u.id === id);
  modal(
    `<span class="eyebrow">PERSONNEL ORDER</span><h2 id="modal-title">${esc(u.username)} 的人事命令</h2><form id="member-edit-form" data-id="${id}"><label>累積咖啡豆 EXP<input type="number" name="exp" min="0" max="1000000" required value="${u.exp}"></label><label>帳號權限<select name="role"><option value="member" ${u.role === "member" ? "selected" : ""}>一般會員</option><option value="admin" ${u.role === "admin" ? "selected" : ""}>管理員</option></select></label><label class="checkbox-label"><input type="checkbox" name="banned" ${u.banned ? "checked" : ""}>封鎖這個帳號</label><label>特任軍階<select name="rank_override"><option value="">依 EXP 自動晉升</option>${state.ranks.map((r) => `<option value="${r.id}" ${u.rank_override === r.id ? "selected" : ""}>${esc(r.name)}</option>`).join("")}</select></label><p class="muted small-text">變更會留下操作紀錄。無法封鎖自己或移除最後一位管理員。</p><div class="form-error" role="alert"></div><button class="button primary full">發布人事命令 ${icon("check")}</button></form>`,
  );
}
function confirmAction(title, text, callback) {
  modal(
    `<h2 id="modal-title">${esc(title)}</h2><p>${esc(text)}</p><div class="confirm-actions"><button class="button outline" data-close>取消</button><button class="button primary" id="confirm-action">確認執行</button></div>`,
  );
  $("#confirm-action").onclick = async () => {
    try {
      await callback();
      closeModal();
    } catch (e) {
      toast(e.message, true);
    }
  };
}
function showSearch() {
  modal(
    `<span class="eyebrow">FIND YOUR LITTLE HAPPINESS</span><h2 id="modal-title">想找些什麼？</h2><label class="sr-only" for="site-search">搜尋活動與話題</label><input id="site-search" type="search" placeholder="搜尋活動、討論話題…" autocomplete="off"><div id="search-results" class="search-results"><p class="empty-small">輸入關鍵字，找找活動和咖啡桌邊的話題。</p></div>`,
  );
}

document.addEventListener("click", async (ev) => {
  const el = ev.target.closest("button,a");
  if (!el) return;
  if (
    el.matches('a[href^="/"]') &&
    !el.getAttribute("href").startsWith("/verify/") &&
    !ev.metaKey &&
    !ev.ctrlKey &&
    !ev.shiftKey
  ) {
    ev.preventDefault();
    closeModal();
    go(el.getAttribute("href"));
    return;
  }
  try {
    if (el.hasAttribute("data-close")) return closeModal();
    if (el.hasAttribute("data-go")) return go(el.dataset.go);
    if (el.hasAttribute("data-auth"))
      return showAuth(el.dataset.auth || "login");
    if (el.hasAttribute("data-demo")) {
      let admin = el.dataset.demo === "admin";
      $("#auth-username").value = admin ? "commander" : "chino";
      $("#auth-password").value = admin ? "Rabbit2026!" : "Chino2026!";
      $("#auth-form").requestSubmit();
      return;
    }
    if (el.id === "sidebar-close") {
      $("#sidebar").classList.remove("open");
      $("#menu-toggle").setAttribute("aria-expanded", "false");
      $("#menu-toggle").focus();
      return;
    }
    if (el.id === "menu-toggle") {
      let open = $("#sidebar").classList.toggle("open");
      el.setAttribute("aria-expanded", open);
      return;
    }
    if (el.id === "search-trigger") return showSearch();
    if (el.id === "notification-trigger") {
      forumFilter = "司令部廣播";
      history.pushState({}, "", "/forum");
      return render();
    }
    if (el.hasAttribute("data-filter")) {
      currentFilter = el.dataset.filter;
      return render();
    }
    if (el.hasAttribute("data-forum-filter")) {
      forumFilter = el.dataset.forumFilter;
      return render();
    }
    if (el.hasAttribute("data-new-post")) return newPost();
    if (el.hasAttribute("data-edit-profile")) return editProfile();
    if (el.hasAttribute("data-logout")) {
      await api("/api/auth/logout", "POST", {});
      await sync();
      go("/");
      toast("已登出，期待下次再相見。");
      return;
    }
    if (el.hasAttribute("data-checkin")) {
      if (!requireUser()) return;
      el.disabled = true;
      const r = await api("/api/checkin", "POST", {});
      await sync();
      await render();
      toast(r.message || "簽到成功！收到了 20 顆咖啡豆。");
      return;
    }
    if (el.hasAttribute("data-event-register")) {
      if (!requireUser()) return;
      const r = await api(
        `/api/events/${el.dataset.eventRegister}/register`,
        "POST",
        {},
      );
      await sync();
      await render();
      toast(r.message || "報名成功，期待和你相聚。");
      return;
    }
    if (el.hasAttribute("data-event-cancel"))
      return confirmAction(
        "取消活動報名",
        "確定要取消這次活動報名嗎？",
        async () => {
          await api(`/api/events/${el.dataset.eventCancel}/register`, "DELETE");
          await sync();
          await render();
          toast("已取消報名。");
        },
      );
    if (el.hasAttribute("data-like")) {
      if (!requireUser()) return;
      await api(`/api/posts/${el.dataset.like}/like`, "POST", {});
      await sync();
      return render();
    }
    if (el.hasAttribute("data-admin-tab")) {
      adminTab = el.dataset.adminTab;
      return adminPage();
    }
    if (el.hasAttribute("data-admin-new-event")) return adminEventForm();
    if (el.hasAttribute("data-admin-edit-event"))
      return adminEventForm(Number(el.dataset.adminEditEvent));
    if (el.hasAttribute("data-admin-close-event"))
      return confirmAction(
        "下架這個活動",
        "活動會停止接受新的報名，既有參與紀錄會保留。",
        async () => {
          await api(
            `/api/admin/events/${el.dataset.adminCloseEvent}`,
            "DELETE",
          );
          await sync();
          await adminPage();
          toast("活動已下架。");
        },
      );
    if (el.hasAttribute("data-edit-member"))
      return editMember(Number(el.dataset.editMember));
    if (el.hasAttribute("data-new-announcement")) {
      modal(
        `<span class="eyebrow">COMMAND BROADCAST</span><h2 id="modal-title">發布司令部廣播</h2><form id="announcement-form"><label>廣播標題<input name="title" required maxlength="120"></label><label>公告內容<textarea name="content" required rows="7" maxlength="10000"></textarea></label><div class="form-error" role="alert"></div><button class="button primary">發布置頂廣播 ${icon("bell")}</button></form>`,
        true,
      );
      return;
    }
    if (el.hasAttribute("data-pin-post") || el.hasAttribute("data-lock-post")) {
      const id = Number(el.dataset.pinPost || el.dataset.lockPost),
        p = adminData.posts.find((p) => p.id === id);
      await api(
        `/api/admin/posts/${id}`,
        "PATCH",
        el.hasAttribute("data-pin-post")
          ? { is_pinned: !p.is_pinned }
          : { locked: !p.locked },
      );
      await sync();
      return adminPage();
    }
    if (el.hasAttribute("data-delete-post"))
      return confirmAction(
        "刪除這個話題",
        "這會刪除話題及其留言，操作無法復原。",
        async () => {
          await api(`/api/admin/posts/${el.dataset.deletePost}`, "DELETE");
          await sync();
          await adminPage();
          toast("話題已刪除。");
        },
      );
  } catch (e) {
    toast(e.message, true);
    if (el.hasAttribute("data-checkin")) el.disabled = false;
  }
});
document.addEventListener("submit", async (ev) => {
  const f = ev.target;
  if (!(f instanceof HTMLFormElement)) return;
  ev.preventDefault();
  const b = $('button[type="submit"],button:not([type])', f),
    err = $(".form-error", f);
  if (b) b.disabled = true;
  if (err) err.textContent = "";
  const data = Object.fromEntries(new FormData(f));
  try {
    if (f.id === "auth-form") {
      data.remember = !!data.remember;
      const r = await api(`/api/auth/${f.dataset.mode}`, "POST", data);
      if (f.dataset.mode === "register") {
        await sync();
        renderShell();
        modal(
          `<div class="auth-logo">${rabbit}</div><h2 id="modal-title">你的第一杯咖啡，準備好了。</h2><p>${esc(r.message || "請前往信箱開啟驗證連結，再登入開始應援旅程。")}</p>${r.demo_verify_url ? `<a href="${esc(r.demo_verify_url)}" class="button primary full" id="demo-verify-link">預覽模式：完成 Email 驗證 ${icon("arrow")}</a><p class="muted small-text">正式環境會透過 Email 寄出這個連結。</p>` : ""}<button class="button outline full" data-auth>前往登入</button>`,
        );
      } else {
        closeModal();
        await sync();
        await render();
        toast("歡迎回到 Rabbit House。");
      }
      return;
    }
    if (f.id === "new-post-form") {
      const r = await api("/api/posts", "POST", data);
      closeModal();
      await sync();
      go(`/forum/${r.id || r.post?.id || r.post_id}`);
      toast(r.message || "話題已發布。");
      return;
    }
    if (f.id === "comment-form") {
      await api(`/api/posts/${f.dataset.postId}/comments`, "POST", data);
      await sync();
      await render();
      toast("回覆已送出。");
      return;
    }
    if (f.id === "profile-form") {
      await api("/api/profile", "PATCH", data);
      closeModal();
      await sync();
      await render();
      toast("軍籍資料已更新。");
      return;
    }
    if (f.id === "admin-event-form") {
      for (const k of ["reward_exp", "min_exp", "capacity"])
        data[k] = Number(data[k]);
      for (const k of ["start_time", "end_time"])
        if (data[k] && !/[Z+-]\d\d:?\d\d$/.test(data[k]))
          data[k] += ":00+08:00";
      await api(
        `/api/admin/events${f.dataset.id ? "/" + f.dataset.id : ""}`,
        f.dataset.id ? "PATCH" : "POST",
        data,
      );
      closeModal();
      await sync();
      await adminPage();
      toast("活動已儲存。");
      return;
    }
    if (f.classList.contains("award-form")) {
      const ids = new FormData(f).getAll("user_ids").map(Number);
      if (!ids.length) throw Error("請先勾選已完成參與的隊員。");
      const r = await api(
        `/api/admin/events/${f.dataset.eventId}/award`,
        "POST",
        { user_ids: ids },
      );
      await sync();
      await adminPage();
      toast(r.message || "出席已確認，獎勵已發放。");
      return;
    }
    if (f.id === "member-edit-form") {
      data.exp = Number(data.exp);
      data.banned = !!data.banned;
      data.rank_override = data.rank_override
        ? Number(data.rank_override)
        : null;
      await api(`/api/admin/users/${f.dataset.id}`, "PATCH", data);
      closeModal();
      await sync();
      await adminPage();
      toast("人事命令已發布。");
      return;
    }
    if (f.id === "announcement-form") {
      await api("/api/admin/announcements", "POST", data);
      closeModal();
      await sync();
      await adminPage();
      toast("司令部廣播已發布。");
      return;
    }
  } catch (e) {
    if (err) err.textContent = e.message;
    else toast(e.message, true);
  } finally {
    if (b?.isConnected) b.disabled = false;
  }
});
document.addEventListener("input", (ev) => {
  if (ev.target.id === "member-search")
    $("#member-rows").innerHTML = userRows(
      adminData.users.filter((u) =>
        (u.username + " " + u.email)
          .toLowerCase()
          .includes(ev.target.value.toLowerCase()),
      ),
    );
  if (ev.target.id === "site-search") {
    const q = ev.target.value.trim().toLowerCase();
    const es = state.events.filter((e) =>
      (e.title + e.description).toLowerCase().includes(q),
    );
    const ps = state.posts.filter((p) =>
      (p.title + p.content).toLowerCase().includes(q),
    );
    $("#search-results").innerHTML = !q
      ? '<p class="empty-small">輸入關鍵字，開始尋找。</p>'
      : es.length + ps.length
        ? es
            .map(
              (e) =>
                `<a href="/events/${e.id}">${icon("calendar")}<span>${esc(e.title)}<small>應援活動 · ${date(e.start_time)}</small></span>${icon("arrow")}</a>`,
            )
            .join("") +
          ps
            .map(
              (p) =>
                `<a href="/forum/${p.id}">${icon("forum")}<span>${esc(p.title)}<small>論壇話題 · ${esc(p.author)}</small></span>${icon("arrow")}</a>`,
            )
            .join("")
        : '<p class="empty-small">沒有找到相關內容，換個關鍵字試試吧。</p>';
  }
});
$("#modal-backdrop").addEventListener("click", (e) => {
  if (e.target.id === "modal-backdrop") closeModal();
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    $("#sidebar").classList.remove("open");
    if (!$("#modal-backdrop").hidden) closeModal();
  }
  if (e.key === "Tab" && !$("#modal-backdrop").hidden) {
    const fs = $$("button,input,textarea,select,a[href]", $("#modal")).filter(
      (x) => !x.disabled && x.offsetParent !== null,
    );
    if (!fs.length) return;
    const first = fs[0],
      last = fs.at(-1);
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
});
window.addEventListener("popstate", () => {
  closeModal();
  render();
});
$("#brand-mark").innerHTML = rabbit;
$("#help-icon").innerHTML = icon("book");
$("#menu-toggle").innerHTML = icon("menu");
$("#search-trigger").innerHTML =
  icon("search") + "<span>找找喜歡的事…</span><kbd>⌕</kbd>";
$("#notification-trigger").innerHTML = icon("bell") + "<i></i>";
(async () => {
  try {
    await sync();
    await render();
    const q = new URLSearchParams(location.search);
    if (q.has("verified") && state.user?.verified)
      toast("Email 驗證已完成，歡迎加入親衛隊。");
    if (q.get("verification") === "expired")
      toast("驗證連結已過期，請使用有效的驗證連結。", true);
  } catch (e) {
    $("#main").innerHTML = errorPage(e.message);
  }
})();

function showPromotion(rank) {
  modal(
    `<span class="eyebrow">PERSONNEL PROMOTION ORDER</span><h2 id="modal-title">人事晉升令</h2><div class="promotion-badge">${badge(rank, true)}</div><p>你的每一份陪伴，都被好好記住。</p><h3>正式晉升為「${esc(rank.name)}」</h3><button class="button primary full" data-close>收下這份榮耀 ${icon("star")}</button>`,
  );
}
