"""
FastAPI main application — CART Election Prediction System backend.
"""
import os
import io
import json
import traceback
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend import auth as auth_module
from backend.ml import data_gen, train as train_module, predict as predict_module
from backend.report import generate_pdf_report

# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="CART Election Prediction System",
    description="AI-powered student government election outcome predictor using Decision Tree (CART).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/app", tags=["Frontend"], include_in_schema=False)
def serve_frontend():
    """Serve the frontend SPA."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ── Helper ─────────────────────────────────────────────────────
def _get_token(authorization: Optional[str]) -> Optional[str]:
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def _require_auth(authorization: Optional[str]) -> dict:
    token = _get_token(authorization)
    user = auth_module.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


# ── Auth Models ────────────────────────────────────────────────
class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=6)


# ── Candidate Model ────────────────────────────────────────────
class CandidateInput(BaseModel):
    candidate_name:   str   = Field(..., example="Alex Johnson")
    popularity_score: float = Field(..., ge=0, le=100, example=75.5)
    campaign_spending: float = Field(..., ge=0, example=12000)
    social_media_score: float = Field(..., ge=0, le=100, example=68.0)
    department:       str   = Field(..., example="Engineering")
    past_performance: float = Field(..., ge=0, le=100, example=60.0)
    engagement_level: float = Field(..., ge=0, le=100, example=80.0)
    model_type:       str   = Field(default="cart", example="cart")   # cart | rf


# ═══════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/auth/signup", tags=["Authentication"])
def signup(req: AuthRequest):
    result = auth_module.signup(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/auth/login", tags=["Authentication"])
def login(req: AuthRequest):
    result = auth_module.login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result


@app.post("/auth/logout", tags=["Authentication"])
def logout(authorization: Optional[str] = Header(default=None)):
    token = _get_token(authorization)
    if token:
        auth_module.logout(token)
    return {"success": True, "message": "Logged out."}


@app.get("/auth/me", tags=["Authentication"])
def me(authorization: Optional[str] = Header(default=None)):
    user = _require_auth(authorization)
    return {"username": user["username"], "role": user["role"]}


# ═══════════════════════════════════════════════════════════════
# DATASET ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/sample-data", tags=["Dataset"])
def get_sample_data():
    """Download the sample CSV dataset."""
    df = data_gen.generate_sample_dataset()
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_election_data.csv"}
    )


@app.post("/upload-dataset", tags=["Dataset"])
async def upload_dataset(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(default=None),
):
    """Upload a CSV dataset for training."""
    _require_auth(authorization)
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    content = await file.read()
    save_path = os.path.join(UPLOAD_DIR, "uploaded_dataset.csv")
    with open(save_path, "wb") as f:
        f.write(content)
    df = pd.read_csv(io.BytesIO(content))
    return {
        "success": True,
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
    }


# ═══════════════════════════════════════════════════════════════
# TRAINING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.post("/train-model", tags=["Model"])
def train_model(authorization: Optional[str] = Header(default=None)):
    """Train CART + Random Forest on uploaded dataset (or sample data)."""
    _require_auth(authorization)
    try:
        uploaded = os.path.join(UPLOAD_DIR, "uploaded_dataset.csv")
        if os.path.exists(uploaded):
            df = pd.read_csv(uploaded)
        else:
            df = data_gen.generate_sample_dataset()

        result = train_module.train(df)
        predict_module.reload_models()
        return result
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# PREDICTION ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.post("/predict", tags=["Prediction"])
def predict(candidate: CandidateInput, authorization: Optional[str] = Header(default=None)):
    """Predict election outcome for a candidate."""
    _require_auth(authorization)
    try:
        data = candidate.dict()
        result = predict_module.predict(data, model_type=data.get("model_type", "cart"))
        # Attach input data for PDF report
        result.update({
            "popularity_score":    candidate.popularity_score,
            "campaign_spending":   candidate.campaign_spending,
            "social_media_score":  candidate.social_media_score,
            "department":          candidate.department,
            "past_performance":    candidate.past_performance,
            "engagement_level":    candidate.engagement_level,
        })
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# METRICS & VISUALIZATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/model-metrics", tags=["Model"])
def model_metrics(authorization: Optional[str] = Header(default=None)):
    """Return saved model evaluation metrics."""
    _require_auth(authorization)
    result = train_module.get_saved_metrics()
    if result.get("status") == "not_trained":
        raise HTTPException(status_code=400, detail="Model not trained yet.")
    return result


@app.get("/model-status", tags=["Model"])
def model_status():
    """Public endpoint — returns whether the model has been trained."""
    return {"trained": train_module.is_trained()}


# ═══════════════════════════════════════════════════════════════
# PDF REPORT ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.post("/generate-report", tags=["Report"])
def generate_report(
    candidate: CandidateInput,
    authorization: Optional[str] = Header(default=None),
):
    """Generate and download a PDF prediction report."""
    _require_auth(authorization)
    try:
        data = candidate.dict()
        prediction = predict_module.predict(data)
        prediction.update({
            "popularity_score":   candidate.popularity_score,
            "campaign_spending":  candidate.campaign_spending,
            "social_media_score": candidate.social_media_score,
            "department":         candidate.department,
            "past_performance":   candidate.past_performance,
            "engagement_level":   candidate.engagement_level,
        })
        pdf_bytes = generate_pdf_report(prediction)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; filename="election_report_{candidate.candidate_name.replace(" ","_")}.pdf"'
            }
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── Root health check ──────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {"message": "CART Election Prediction API is running.", "version": "1.0.0"}
