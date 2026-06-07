"""
ML Training pipeline: CART (Decision Tree) + Random Forest with visualizations.
"""
import os
import io
import base64
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report
)

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

FEATURE_COLS = [
    "popularity_score", "campaign_spending", "social_media_score",
    "department", "past_performance", "engagement_level"
]
TARGET_COL = "election_result"

CART_PATH   = os.path.join(MODEL_DIR, "cart_model.joblib")
RF_PATH     = os.path.join(MODEL_DIR, "rf_model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
ENCODER_PATH = os.path.join(MODEL_DIR, "encoder.joblib")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.joblib")


# ──────────────────────────────────────────────────────────────
def _preprocess(df: pd.DataFrame, le: LabelEncoder = None, scaler: StandardScaler = None, fit: bool = True):
    df = df.copy()

    # Drop rows with nulls in target
    if TARGET_COL in df.columns:
        df = df.dropna(subset=[TARGET_COL])

    # Fill numeric nulls with median
    num_cols = ["popularity_score", "campaign_spending", "social_media_score",
                "past_performance", "engagement_level"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(df[c].median())

    # Encode department
    if "department" not in df.columns:
        df["department"] = "Engineering"
    df["department"] = df["department"].astype(str).fillna("Unknown")

    if fit:
        le = LabelEncoder()
        df["department"] = le.fit_transform(df["department"])
    else:
        df["department"] = le.transform(df["department"])

    X = df[FEATURE_COLS].values.astype(float)

    if fit:
        scaler = StandardScaler()
        X = scaler.fit_transform(X)
    else:
        X = scaler.transform(X)

    y = None
    if TARGET_COL in df.columns:
        y = df[TARGET_COL].values.astype(int)

    return X, y, le, scaler


# ──────────────────────────────────────────────────────────────
def _fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=120, facecolor="#0a0e1a")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


# ──────────────────────────────────────────────────────────────
def train(df: pd.DataFrame, model_type: str = "cart") -> dict:
    X, y, le, scaler = _preprocess(df, fit=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ── CART ──────────────────────────────────────────────────
    cart = DecisionTreeClassifier(criterion="gini", max_depth=5, random_state=42)
    cart.fit(X_train, y_train)
    cart_pred = cart.predict(X_test)

    # ── Random Forest ─────────────────────────────────────────
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)

    # ── Metrics ───────────────────────────────────────────────
    def _metrics(y_true, y_pred, name):
        return {
            "model": name,
            "accuracy":  round(accuracy_score(y_true, y_pred), 4),
            "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
            "recall":    round(recall_score(y_true, y_pred, zero_division=0), 4),
            "f1_score":  round(f1_score(y_true, y_pred, zero_division=0), 4),
        }

    cart_metrics = _metrics(y_test, cart_pred, "CART (Decision Tree)")
    rf_metrics   = _metrics(y_test, rf_pred,   "Random Forest")

    # ── Confusion Matrix (CART) ───────────────────────────────
    cm = confusion_matrix(y_test, cart_pred)
    fig_cm, ax = plt.subplots(figsize=(5, 4))
    fig_cm.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Lost", "Won"], yticklabels=["Lost", "Won"],
                ax=ax, linewidths=0.5)
    ax.set_xlabel("Predicted", color="#a0aec0")
    ax.set_ylabel("Actual", color="#a0aec0")
    ax.set_title("Confusion Matrix – CART", color="#e2e8f0", pad=12)
    ax.tick_params(colors="#a0aec0")
    cm_b64 = _fig_to_b64(fig_cm)
    plt.close(fig_cm)

    # ── Decision Tree Diagram ─────────────────────────────────
    fig_tree, ax2 = plt.subplots(figsize=(18, 8))
    fig_tree.patch.set_facecolor("#0a0e1a")
    ax2.set_facecolor("#0a0e1a")
    plot_tree(
        cart, feature_names=FEATURE_COLS, class_names=["Lost", "Won"],
        filled=True, rounded=True, ax=ax2, fontsize=8,
        impurity=True, proportion=False
    )
    ax2.set_title("Decision Tree (CART) – Gini Index", color="#e2e8f0", pad=15, fontsize=13)
    tree_b64 = _fig_to_b64(fig_tree)
    plt.close(fig_tree)

    # ── Feature Importance ────────────────────────────────────
    importances = cart.feature_importances_
    fi_df = pd.DataFrame({"feature": FEATURE_COLS, "importance": importances})
    fi_df = fi_df.sort_values("importance", ascending=True)

    fig_fi, ax3 = plt.subplots(figsize=(7, 4))
    fig_fi.patch.set_facecolor("#0a0e1a")
    ax3.set_facecolor("#111827")
    colors = plt.cm.cool(np.linspace(0.3, 0.9, len(fi_df)))
    bars = ax3.barh(fi_df["feature"], fi_df["importance"], color=colors)
    ax3.set_xlabel("Importance Score", color="#a0aec0")
    ax3.set_title("Feature Importance – CART", color="#e2e8f0", pad=12)
    ax3.tick_params(colors="#a0aec0")
    ax3.spines[:].set_color("#2d3748")
    for bar, val in zip(bars, fi_df["importance"]):
        ax3.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
                 f"{val:.3f}", va="center", color="#e2e8f0", fontsize=8)
    fi_b64 = _fig_to_b64(fig_fi)
    plt.close(fig_fi)

    # ── Save artefacts ────────────────────────────────────────
    joblib.dump(cart,  CART_PATH)
    joblib.dump(rf,    RF_PATH)
    joblib.dump(le,    ENCODER_PATH)
    joblib.dump(scaler, SCALER_PATH)

    result = {
        "status": "success",
        "samples_trained": len(X_train),
        "samples_tested": len(X_test),
        "cart_metrics": cart_metrics,
        "rf_metrics": rf_metrics,
        "confusion_matrix_b64": cm_b64,
        "decision_tree_b64": tree_b64,
        "feature_importance_b64": fi_b64,
        "feature_importances": dict(zip(FEATURE_COLS, [round(v, 4) for v in importances])),
    }
    joblib.dump(result, METRICS_PATH)
    return result


# ──────────────────────────────────────────────────────────────
def get_saved_metrics() -> dict:
    if os.path.exists(METRICS_PATH):
        return joblib.load(METRICS_PATH)
    return {"status": "not_trained"}


# ──────────────────────────────────────────────────────────────
def is_trained() -> bool:
    return os.path.exists(CART_PATH) and os.path.exists(SCALER_PATH)
