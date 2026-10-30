# -*- coding: utf-8 -*-
"""API router for UPI payment screenshot analysis."""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import Dict, Any

from ..services.screenshot_service import analyze_screenshot
from ..services.auth_service import get_current_user
from ..services.incident_service import increment_screenshot_counter
from ..services.scan_history_service import save_screenshot_scan

router = APIRouter(prefix="/api/screenshot", tags=["Screenshot"])

MAX_SCREENSHOT_SIZE = 15 * 1024 * 1024  # 15 MB limit
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


@router.post("/analyze")
async def analyze_screenshot_endpoint(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a UPI payment screenshot for dataset-driven reference analysis.
    Requires authenticated SignalSafe session.
    Validates file format (PNG, JPG, JPEG, WEBP) and file size (<= 15MB).
    Persists scan result to PostgreSQL and increments counter.
    """
    # 1. Filename extension check
    filename_lower = (file.filename or "").lower()
    if not any(filename_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PNG, JPG, or JPEG image.",
        )

    # 2. File size check
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty.",
        )
    if len(image_bytes) > MAX_SCREENSHOT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_SCREENSHOT_SIZE // (1024 * 1024)} MB.",
        )

    # 3. Perform dataset-driven screenshot analysis
    result = analyze_screenshot(image_bytes)

    # 4. Persist actual detection result to dedicated PostgreSQL
    scan_id = save_screenshot_scan(result, current_user)
    if scan_id:
        result["scan_id"] = scan_id

    # 5. Increment verified persistent counter
    increment_screenshot_counter()

    return result
