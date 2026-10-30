# -*- coding: utf-8 -*-
"""API router for QR code analysis."""

from fastapi import APIRouter, UploadFile, File, Depends
from ..services.qrcode_service import analyze_qrcode
from ..services.auth_service import get_current_user
from ..services.scan_history_service import save_qr_scan

router = APIRouter(prefix="/api/qrcode", tags=["QR Code"])


@router.post("/analyze")
async def analyze_qrcode_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a QR code image for UPI fraud analysis.
    Requires authenticated SignalSafe session.
    Returns risk_score (0-100), status, decoded_data, and reasons.
    Persists actual QR scan result to dedicated PostgreSQL.
    """
    image_bytes = await file.read()
    result = analyze_qrcode(image_bytes)

    # Persist actual QR detection result to dedicated PostgreSQL
    scan_id = save_qr_scan(result, current_user)
    if scan_id:
        result["scan_id"] = scan_id

    return result
