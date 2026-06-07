/* ─────────────────────────────────────────────────
   dashboard.js  —  Home Dashboard
───────────────────────────────────────────────── */

async function loadDashboard() {
  if (!state.token) return;

  // Refresh model status
  await checkModelStatus();

  // Load metrics if trained
  if (state.modelTrained && !state.metricsCache) {
    try {
      state.metricsCache = await apiGet("/model-metrics");
    } catch (_) {}
  }

  renderDashboard();
}

function renderDashboard() {
  const m = state.metricsCache;
  const cartM = m?.cart_metrics || null;

  // ── Stat cards ─────────────────────────────────────────
  document.getElementById("dash-accuracy").textContent =
    cartM ? (cartM.accuracy * 100).toFixed(1) + "%" : "—";
  document.getElementById("dash-f1").textContent =
    cartM ? (cartM.f1_score * 100).toFixed(1) + "%" : "—";
  document.getElementById("dash-samples").textContent =
    m ? (m.samples_trained + m.samples_tested) : "—";
  document.getElementById("dash-status").textContent =
    state.modelTrained ? "Trained ✓" : "Not Trained";

  // ── Metrics comparison ──────────────────────────────────
  if (cartM) {
    renderComparisonBars(m);
    document.getElementById("dash-metrics-section").style.display = "block";
  } else {
    document.getElementById("dash-metrics-section").style.display = "none";
  }
}

function renderComparisonBars(m) {
  const cart = m.cart_metrics;
  const rf   = m.rf_metrics;

  const bars = [
    { label: "Accuracy",  cart: cart.accuracy,  rf: rf.accuracy  },
    { label: "Precision", cart: cart.precision, rf: rf.precision },
    { label: "Recall",    cart: cart.recall,    rf: rf.recall    },
    { label: "F1 Score",  cart: cart.f1_score,  rf: rf.f1_score  },
  ];

  // CART bars
  const cartEl = document.getElementById("cart-bars");
  cartEl.innerHTML = bars.map(b => `
    <div class="comparison-row">
      <div class="comparison-label">${b.label}</div>
      <div class="comparison-bar-track">
        <div class="comparison-bar-fill" style="width:${b.cart*100}%; background: linear-gradient(90deg, var(--accent), var(--accent-2));"></div>
      </div>
      <div class="comparison-val">${(b.cart*100).toFixed(1)}%</div>
    </div>
  `).join("");

  // RF bars
  const rfEl = document.getElementById("rf-bars");
  rfEl.innerHTML = bars.map(b => `
    <div class="comparison-row">
      <div class="comparison-label">${b.label}</div>
      <div class="comparison-bar-track">
        <div class="comparison-bar-fill" style="width:${b.rf*100}%; background: linear-gradient(90deg, #059669, #10b981);"></div>
      </div>
      <div class="comparison-val">${(b.rf*100).toFixed(1)}%</div>
    </div>
  `).join("");
}

/* ── Train button ──────────────────────────────────────── */
document.getElementById("btn-train").addEventListener("click", async () => {
  if (!state.token) return toast("Please log in first.", "error");
  setLoading(true, "Training CART & Random Forest models…");
  try {
    const result = await apiPost("/train-model", {});
    state.modelTrained = true;
    state.metricsCache = result;
    await checkModelStatus();
    renderDashboard();
    toast(`Models trained! CART Accuracy: ${(result.cart_metrics.accuracy * 100).toFixed(1)}%`, "success", 5000);
  } catch (err) {
    toast("Training failed: " + err.message, "error");
  } finally {
    setLoading(false);
  }
});

/* ── Quick predict from dashboard ──────────────────────── */
document.getElementById("btn-quick-predict").addEventListener("click", () => {
  showPage("predict");
});
