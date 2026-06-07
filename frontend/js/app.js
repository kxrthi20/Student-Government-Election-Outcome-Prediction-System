/* ─────────────────────────────────────────────────────────
   app.js  —  SPA Router + Global State + API helpers
───────────────────────────────────────────────────────── */

const API = "http://127.0.0.1:8000";

/* ── State ─────────────────────────────────────────────── */
const state = {
  token:     localStorage.getItem("token") || null,
  username:  localStorage.getItem("username") || null,
  role:      localStorage.getItem("role") || null,
  modelTrained: false,
  lastPrediction: null,
  metricsCache: null,
};

/* ── Toast ─────────────────────────────────────────────── */
function toast(message, type = "info", duration = 3500) {
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${message}</span>`;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), duration);
}

/* ── Loading overlay ───────────────────────────────────── */
function setLoading(show, msg = "Processing…") {
  const o = document.getElementById("loading-overlay");
  o.querySelector("p").textContent = msg;
  o.classList.toggle("show", show);
}

/* ── HTTP helpers ──────────────────────────────────────── */
async function apiPost(path, body, auth = true) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(API + path, { method: "POST", headers, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

async function apiGet(path, auth = true) {
  const headers = {};
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(API + path, { headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

async function apiDownload(path, method = "GET", body = null, filename = "download") {
  const headers = {};
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  if (body) headers["Content-Type"] = "application/json";
  const res = await fetch(API + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Download failed");
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/* ── Router ────────────────────────────────────────────── */
const pages = document.querySelectorAll(".page");
const navItems = document.querySelectorAll(".nav-item[data-page]");

function showPage(id) {
  pages.forEach(p => p.classList.toggle("active", p.id === `page-${id}`));
  navItems.forEach(n => n.classList.toggle("active", n.dataset.page === id));
  document.getElementById("topbar-title").textContent = {
    dashboard: "Dashboard",
    predict:   "New Prediction",
    results:   "Prediction Results",
    insights:  "Model Insights",
    data:      "Dataset Manager",
  }[id] || id;
}

navItems.forEach(n => {
  n.addEventListener("click", () => {
    const p = n.dataset.page;
    if (p === "insights")  loadInsights();
    if (p === "dashboard") loadDashboard();
    showPage(p);
  });
});

/* ── Auth guard ────────────────────────────────────────── */
function checkAuth() {
  if (state.token) {
    document.getElementById("auth-page").style.display = "none";
    document.getElementById("app-shell").style.display = "flex";
    document.getElementById("nav-username").textContent = state.username || "User";
    document.getElementById("nav-role").textContent = state.role || "user";
    document.getElementById("nav-avatar").textContent = (state.username || "U")[0].toUpperCase();
    document.getElementById("topbar-username").textContent = state.username;
    loadDashboard();
    checkModelStatus();
  } else {
    document.getElementById("auth-page").style.display = "flex";
    document.getElementById("app-shell").style.display = "none";
  }
}

function setSession(data) {
  state.token    = data.token;
  state.username = data.username;
  state.role     = data.role;
  localStorage.setItem("token",    data.token);
  localStorage.setItem("username", data.username);
  localStorage.setItem("role",     data.role);
}

function clearSession() {
  state.token = state.username = state.role = null;
  localStorage.removeItem("token");
  localStorage.removeItem("username");
  localStorage.removeItem("role");
}

/* ── Model status ──────────────────────────────────────── */
async function checkModelStatus() {
  try {
    const data = await apiGet("/model-status", false);
    state.modelTrained = data.trained;
    const pill = document.getElementById("model-status-pill");
    if (data.trained) {
      pill.className = "status-pill trained";
      pill.innerHTML = '<span class="status-dot"></span> Model Ready';
    } else {
      pill.className = "status-pill not-trained";
      pill.innerHTML = '<span class="status-dot"></span> Not Trained';
    }
  } catch (_) {}
}

/* ── Logout ────────────────────────────────────────────── */
document.getElementById("btn-logout").addEventListener("click", async () => {
  try { await apiPost("/auth/logout", {}, true); } catch (_) {}
  clearSession();
  checkAuth();
  toast("Logged out successfully.", "success");
});

/* ── Boot ──────────────────────────────────────────────── */
window.addEventListener("DOMContentLoaded", () => {
  checkAuth();
  showPage("dashboard");
});
