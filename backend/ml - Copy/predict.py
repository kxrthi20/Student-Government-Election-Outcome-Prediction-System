"""
Prediction logic — loads saved CART / RF models and returns predictions.
"""
import os
import joblib
import numpy as np
import pandas as pd

from .train import CART_PATH, RF_PATH, SCALER_PATH, ENCODER_PATH, FEATURE_COLS, is_trained

_cache = {}


def _load_models():
    global _cache
    if not _cache:
        _cache["cart"]    = joblib.load(CART_PATH)
        _cache["rf"]      = joblib.load(RF_PATH)
        _cache["scaler"]  = joblib.load(SCALER_PATH)
        _cache["encoder"] = joblib.load(ENCODER_PATH)
    return _cache


def predict(candidate_data: dict, model_type: str = "cart") -> dict:
    if not is_trained():
        raise RuntimeError("Model not trained yet. Please train the model first.")

    models = _load_models()
    cart    = models["cart"]
    rf      = models["rf"]
    scaler  = models["scaler"]
    le      = models["encoder"]

    # Build single-row DataFrame
    row = {
        "popularity_score":  float(candidate_data.get("popularity_score", 50)),
        "campaign_spending": float(candidate_data.get("campaign_spending", 5000)),
        "social_media_score": float(candidate_data.get("social_media_score", 50)),
        "department":        str(candidate_data.get("department", "Engineering")),
        "past_performance":  float(candidate_data.get("past_performance", 50)),
        "engagement_level":  float(candidate_data.get("engagement_level", 50)),
    }

    df = pd.DataFrame([row])

    # Encode department
    known_classes = list(le.classes_)
    dept = df["department"].values[0]
    if dept not in known_classes:
        dept = known_classes[0]
    df["department"] = le.transform([dept])

    X = df[FEATURE_COLS].values.astype(float)
    X = scaler.transform(X)

    # CART prediction
    cart_pred = int(cart.predict(X)[0])
    cart_proba = cart.predict_proba(X)[0]
    cart_confidence = round(float(max(cart_proba)) * 100, 2)

    # RF comparison
    rf_pred = int(rf.predict(X)[0])
    rf_proba = rf.predict_proba(X)[0]
    rf_confidence = round(float(max(rf_proba)) * 100, 2)

    # Feature importance insight
    importances = cart.feature_importances_
    fi = dict(zip(FEATURE_COLS, [round(float(v), 4) for v in importances]))
    top_factors = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "candidate_name":    candidate_data.get("candidate_name", "Unknown"),
        "cart_prediction":   "WON" if cart_pred == 1 else "LOST",
        "cart_confidence":   cart_confidence,
        "cart_probabilities": {
            "lost": round(float(cart_proba[0]) * 100, 2),
            "won":  round(float(cart_proba[1]) * 100, 2),
        },
        "rf_prediction":     "WON" if rf_pred == 1 else "LOST",
        "rf_confidence":     rf_confidence,
        "rf_probabilities": {
            "lost": round(float(rf_proba[0]) * 100, 2),
            "won":  round(float(rf_proba[1]) * 100, 2),
        },
        "top_influencing_factors": [
            {"feature": f, "importance": v} for f, v in top_factors
        ],
        "feature_importances": fi,
    }


def reload_models():
    global _cache
    _cache = {}
