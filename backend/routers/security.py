# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Security Tools API Router.
Provides centralized endpoints for ML-based Website Safety Checker and
Malicious Link Scanner powered by the trained Linear SVM URL classification model.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Header, status
from pydantic import BaseModel, Field

from ..services.ml_url_service import predict_url_safety
from ..services.scan_history_service import (
    get_url_report_count,
    save_url_scan,
)
from ..services.auth_service import verify_signalsafe_token

router = APIRouter(prefix="/api/security", tags=["Security ML Tools"])


class URLPredictRequest(BaseModel):
    url: str = Field(..., description="Target website or link URL to analyze")
    scan_type: Optional[str] = Field("website", description="'website' for Website Safety Checker or 'link' for Malicious Link Scanner")


def _get_optional_user(request: Request, authorization: Optional[str] = None) -> Optional[dict]:
    """Helper to extract user profile if valid session is present without forcing 401."""
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get("signalsafe_session")
    if token:
        try:
            return verify_signalsafe_token(token)
        except Exception:
            return None
    return None


@router.post("/predict-url")
async def predict_url_endpoint(
    payload: URLPredictRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    """
    Centralized ML URL prediction endpoint for Website Safety Checker & Malicious Link Scanner.
    Executes trained Linear SVM inference on TF-IDF character n-gram features.
    Safe against SSRF: Does NOT connect to or scrape the target website.
    """
    if not payload.url or not payload.url.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required and cannot be empty.",
        )

    scan_type = (payload.scan_type or "website").lower().strip()
    if scan_type not in ("website", "link"):
        scan_type = "website"

    try:
        prediction_result = predict_url_safety(payload.url, scan_type=scan_type)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Machine learning inference failed: {str(exc)}",
        )

    # Optional audit and scan history persistence if user is authenticated
    current_user = _get_optional_user(request, authorization)
    report_count = get_url_report_count(prediction_result["url"])
    prediction_result["report_count"] = report_count

    if current_user:
        try:
            # Map into scan history format
            scan_id = save_url_scan(
                result={
                    "risk_score": prediction_result["risk_score"],
                    "status": prediction_result["status"],
                    "reasons": prediction_result["recommendations"],
                    "extracted_fields": {
                        "classification": prediction_result["classification"],
                        "confidence": prediction_result["confidence_percentage"],
                        "decision_score": prediction_result["decision_score"],
                    },
                },
                url=prediction_result["url"],
                user=current_user,
                report_count=report_count,
            )
            if scan_id:
                prediction_result["scan_id"] = scan_id
        except Exception:
            pass

    return prediction_result

