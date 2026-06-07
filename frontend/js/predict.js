/* ─────────────────────────────────────────────────────────
   predict.js  —  Candidate input form + result rendering
───────────────────────────────────────────────────────── */

/* ── Range sliders ─────────────────────────────────────── */
["popularity", "social_media", "past_performance", "engagement"].forEach(id => {
  const slider = document.getElementById(`f-${id}`);
  const val    = document.getElementById(`f-${id}-val`);
  if (!slider || !val) return;
  val.textContent = slider.value;
  slider.addEventListener("input", () => val.textContent = slider.value);
});

/* ── Form submit ───────────────────────────────────────── */
document.getElementById("predict-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!state.token) return toast("Please log in first.", "error");
  if (!state.modelTrained) {
    toast("Please train the model first (Dashboard → Train Model).", "error", 5000);
    return;
  }

  const payload = {
    candidate_name:     document.getElementById("f-name").value.trim(),
    popularity_score:   parseFloat(document.getElementById("f-popularity").value),
    campaign_spending:  parseFloat(document.getElementById("f-spending").value),
    social_media_score: parseFloat(document.getElementById("f-social_media").value),
    department:         document.getElementById("f-department").value,
    past_performance:   parseFloat(document.getElementById("f-past_performance").value),
    engagement_level:   parseFloat(document.getElementById("f-engagement").value),
    model_type:         document.getElementById("f-model-type").value,
  };

  if (!payload.candidate_name) return toast("Please enter a candidate name.", "error");

  setLoading(true, "Running prediction…");
  try {
    const result = await apiPost("/predict", payload);
    state.lastPrediction = { ...result, ...payload };
    renderResults(result, payload);
    showPage("results");
    toast("Prediction complete!", "success");
  } catch (err) {
    toast("Prediction failed: " + err.message, "error");
  } finally {
    setLoading(false);
  }
});

/* ── Result renderer ───────────────────────────────────── */
function renderResults(data, input) {
  const won = data.cart_prediction === "WON";

  // Verdict
  document.getElementById("res-verdict").textContent     = won ? "🏆 WON" : "❌ LOST";
  document.getElementById("res-verdict").className       = "result-verdict " + (won ? "won" : "lost");
  document.getElementById("res-candidate").textContent   = data.candidate_name;
  document.getElementById("res-subtitle").textContent    =
    `CART predicts this candidate will ${won ? "WIN" : "LOSE"} the election.`;

  // Confidence ring
  const conf = data.cart_confidence;
  renderConfidenceRing("res-ring", conf, won);

  // Probabilities
  document.getElementById("res-prob-won").textContent  = data.cart_probabilities.won.toFixed(1) + "%";
  document.getElementById("res-prob-lost").textContent = data.cart_probabilities.lost.toFixed(1) + "%";
  document.getElementById("res-prob-won-bar").style.width  = data.cart_probabilities.won + "%";
  document.getElementById("res-prob-lost-bar").style.width = data.cart_probabilities.lost + "%";

  // RF comparison
  const rfWon = data.rf_prediction === "WON";
  document.getElementById("rf-verdict").textContent  = rfWon ? "🏆 WON" : "❌ LOST";
  document.getElementById("rf-verdict").style.color  = rfWon ? "var(--success)" : "var(--danger)";
  document.getElementById("rf-confidence").textContent = data.rf_confidence.toFixed(1) + "%";
  renderConfidenceRing("rf-ring", data.rf_confidence, rfWon);

  // Top influencing factors
  const factors = data.top_influencing_factors || [];
  const maxImp  = factors[0]?.importance || 1;
  document.getElementById("factors-list").innerHTML = factors.map((f, i) => `
    <li class="fi-item">
      <div class="fi-rank">${i + 1}</div>
      <div class="fi-name">${f.feature.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</div>
      <div class="fi-bar-wrap">
        <div class="fi-bar" style="width:${(f.importance / maxImp * 100).toFixed(1)}%"></div>
      </div>
      <div class="fi-score">${f.importance.toFixed(4)}</div>
    </li>
  `).join("");

  // Input summary chips
  document.getElementById("res-input-summary").innerHTML = `
    <div class="factor-chip"><div class="fc-label">Popularity</div><div class="fc-val">${input.popularity_score}</div><div class="fc-bar" style="width:${input.popularity_score}%"></div></div>
    <div class="factor-chip"><div class="fc-label">Social Media</div><div class="fc-val">${input.social_media_score}</div><div class="fc-bar" style="width:${input.social_media_score}%"></div></div>
    <div class="factor-chip"><div class="fc-label">Engagement</div><div class="fc-val">${input.engagement_level}</div><div class="fc-bar" style="width:${input.engagement_level}%"></div></div>
    <div class="factor-chip"><div class="fc-label">Past Perf.</div><div class="fc-val">${input.past_performance}</div><div class="fc-bar" style="width:${input.past_performance}%"></div></div>
    <div class="factor-chip"><div class="fc-label">Spending $</div><div class="fc-val">${Number(input.campaign_spending).toLocaleString()}</div><div class="fc-bar"></div></div>
    <div class="factor-chip"><div class="fc-label">Dept.</div><div class="fc-val" style="font-size:12px">${input.department}</div><div class="fc-bar"></div></div>
  `;
}

/* ── SVG confidence ring ───────────────────────────────── */
function renderConfidenceRing(containerId, pct, won) {
  const el = document.getElementById(containerId);
  if (!el) return;
  const r = 54, cx = 65, cy = 65;
  const circumference = 2 * Math.PI * r;
  const dash = (pct / 100) * circumference;
  const color = won ? "#10b981" : "#ef4444";
  el.innerHTML = `
    <svg width="130" height="130" viewBox="0 0 130 130">
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10"/>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}"
        stroke-width="10" stroke-dasharray="${dash} ${circumference}"
        stroke-linecap="round" style="transition: stroke-dasharray 1s ease;"/>
    </svg>
    <div class="ring-val" style="color:${color}">${pct.toFixed(1)}%</div>
    <div class="ring-label">Confidence</div>
  `;
}

/* ── PDF download ──────────────────────────────────────── */
document.getElementById("btn-download-pdf").addEventListener("click", async () => {
  if (!state.lastPrediction) return toast("No prediction to export.", "error");
  const p = state.lastPrediction;
  setLoading(true, "Generating PDF report…");
  try {
    await apiDownload(
      "/generate-report",
      "POST",
      {
        candidate_name:     p.candidate_name,
        popularity_score:   p.popularity_score,
        campaign_spending:  p.campaign_spending,
        social_media_score: p.social_media_score,
        department:         p.department,
        past_performance:   p.past_performance,
        engagement_level:   p.engagement_level,
        model_type:         p.model_type || "cart",
      },
      `election_report_${p.candidate_name.replace(/\s+/g, "_")}.pdf`
    );
    toast("PDF downloaded!", "success");
  } catch (err) {
    toast("PDF failed: " + err.message, "error");
  } finally {
    setLoading(false);
  }
});

/* ── New Prediction button ─────────────────────────────── */
document.getElementById("btn-new-predict").addEventListener("click", () => {
  showPage("predict");
});
