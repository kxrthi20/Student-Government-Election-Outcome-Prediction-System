/* ─────────────────────────────────────────────────────────
   insights.js  —  Model Visualizations + Dataset Manager
───────────────────────────────────────────────────────── */

async function loadInsights() {
  if (!state.token) return;
  if (!state.modelTrained) {
    document.getElementById("insights-empty").style.display = "block";
    document.getElementById("insights-content").style.display = "none";
    return;
  }

  document.getElementById("insights-empty").style.display = "none";
  document.getElementById("insights-content").style.display = "block";

  try {
    const m = state.metricsCache || await apiGet("/model-metrics");
    state.metricsCache = m;
    renderInsights(m);
  } catch (err) {
    toast("Could not load insights: " + err.message, "error");
  }
}

function renderInsights(m) {
  // Confusion matrix
  if (m.confusion_matrix_b64) {
    document.getElementById("img-confusion").src = `data:image/png;base64,${m.confusion_matrix_b64}`;
  }
  // Decision tree
  if (m.decision_tree_b64) {
    document.getElementById("img-tree").src = `data:image/png;base64,${m.decision_tree_b64}`;
  }
  // Feature importance chart
  if (m.feature_importance_b64) {
    document.getElementById("img-fi").src = `data:image/png;base64,${m.feature_importance_b64}`;
  }

  // Feature importance ranked list
  const fi   = m.feature_importances || {};
  const sorted = Object.entries(fi).sort((a, b) => b[1] - a[1]);
  const maxV  = sorted[0]?.[1] || 1;
  document.getElementById("fi-ranked-list").innerHTML = sorted.map(([k, v], i) => `
    <li class="fi-item">
      <div class="fi-rank">${i + 1}</div>
      <div class="fi-name">${k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</div>
      <div class="fi-bar-wrap">
        <div class="fi-bar" style="width:${(v / maxV * 100).toFixed(1)}%"></div>
      </div>
      <div class="fi-score">${v.toFixed(4)}</div>
    </li>
  `).join("");

  // Metrics table
  const cart = m.cart_metrics;
  const rf   = m.rf_metrics;
  document.getElementById("metrics-table-body").innerHTML = `
    <tr>
      <td>Accuracy</td>
      <td><span class="badge badge-success">${(cart.accuracy*100).toFixed(2)}%</span></td>
      <td><span class="badge badge-info">${(rf.accuracy*100).toFixed(2)}%</span></td>
    </tr>
    <tr>
      <td>Precision</td>
      <td>${(cart.precision*100).toFixed(2)}%</td>
      <td>${(rf.precision*100).toFixed(2)}%</td>
    </tr>
    <tr>
      <td>Recall</td>
      <td>${(cart.recall*100).toFixed(2)}%</td>
      <td>${(rf.recall*100).toFixed(2)}%</td>
    </tr>
    <tr>
      <td>F1 Score</td>
      <td>${(cart.f1_score*100).toFixed(2)}%</td>
      <td>${(rf.f1_score*100).toFixed(2)}%</td>
    </tr>
    <tr>
      <td>Train Samples</td>
      <td colspan="2" style="text-align:center">${m.samples_trained}</td>
    </tr>
    <tr>
      <td>Test Samples</td>
      <td colspan="2" style="text-align:center">${m.samples_tested}</td>
    </tr>
  `;
}

/* ── Dataset upload ────────────────────────────────────── */
const uploadInput = document.getElementById("csv-upload-input");
const uploadZone  = document.getElementById("csv-upload-zone");

uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("dragover"); });
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));
uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  const f = e.dataTransfer.files[0];
  if (f) handleUpload(f);
});

uploadInput.addEventListener("change", () => {
  if (uploadInput.files[0]) handleUpload(uploadInput.files[0]);
});

async function handleUpload(file) {
  if (!file.name.endsWith(".csv")) return toast("Only CSV files are accepted.", "error");
  const formData = new FormData();
  formData.append("file", file);
  setLoading(true, "Uploading dataset…");
  try {
    const res = await fetch(`${API}/upload-dataset`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${state.token}` },
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    toast(`Dataset uploaded: ${data.rows} rows, ${data.columns.length} columns.`, "success", 5000);
    document.getElementById("upload-info").innerHTML = `
      <div class="alert alert-success">
        ✅ <strong>${file.name}</strong> uploaded — ${data.rows} rows detected.
        <br><small>Columns: ${data.columns.join(", ")}</small>
      </div>
    `;
  } catch (err) {
    toast("Upload failed: " + err.message, "error");
  } finally {
    setLoading(false);
  }
}

/* ── Sample CSV download ───────────────────────────────── */
document.getElementById("btn-download-sample").addEventListener("click", async () => {
  try {
    await apiDownload("/sample-data", "GET", null, "sample_election_data.csv");
    toast("Sample dataset downloaded!", "success");
  } catch (err) {
    toast("Download failed: " + err.message, "error");
  }
});
