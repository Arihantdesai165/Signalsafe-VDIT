# -*- coding: utf-8 -*-
"""
CyberAdmin Screenshot Dataset Management Router.
Endpoints for uploading, validating, activating, previewing, and deactivating
reference transaction datasets for the SignalSafe Screenshot Detector.
All endpoints require authenticated CyberAdmin role.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import Optional, Dict, Any, List

from ..services.auth_service import require_cyberadmin
from ..services.screenshot_dataset_service import (
    validate_and_parse_csv,
    activate_new_dataset,
    get_active_dataset_info,
    deactivate_active_dataset,
    get_dataset_history,
    MANDATORY_DEMO_NOTICE,
)

router = APIRouter(prefix="/api/cyberadmin/screenshot-datasets", tags=["CyberAdmin Screenshot Datasets"])

MAX_CSV_SIZE = 10 * 1024 * 1024  # 10 MB limit


@router.get("/active")
async def get_active_dataset(
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Get metadata for the currently active screenshot reference dataset.
    Requires CyberAdmin role.
    """
    return get_active_dataset_info()


@router.post("/validate")
async def validate_dataset_csv(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Validate a candidate dataset CSV before activation.
    Performs header verification, type validation, formula-injection guards,
    and duplicate detection.
    Does NOT modify the database or change active state.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are supported for reference datasets.",
        )

    content_bytes = await file.read()
    if len(content_bytes) > MAX_CSV_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_CSV_SIZE // (1024 * 1024)} MB.",
        )

    try:
        csv_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            csv_text = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode CSV file. Please upload a UTF-8 encoded CSV.",
            )

    validation_result = validate_and_parse_csv(csv_text)
    return validation_result


@router.post("/activate")
async def activate_dataset(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Atomically upload, validate, and activate a new reference dataset.
    Deactivates any existing active dataset within the same database transaction.
    Logs an audit event in PostgreSQL.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files (.csv) are supported.",
        )

    content_bytes = await file.read()
    if len(content_bytes) > MAX_CSV_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {MAX_CSV_SIZE // (1024 * 1024)} MB.",
        )

    try:
        csv_text = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            csv_text = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to decode CSV file. Please upload a UTF-8 encoded CSV.",
            )

    result = activate_new_dataset(
        csv_content=csv_text,
        filename=file.filename,
        admin_user=current_user,
        dataset_name=dataset_name,
    )
    return result


@router.get("/history")
async def get_history(
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Retrieve chronological dataset version history for CyberAdmin audit review.
    """
    history = get_dataset_history()
    return {
        "history": history,
        "total_versions": len(history),
        "demo_notice": MANDATORY_DEMO_NOTICE,
    }


@router.post("/deactivate")
@router.delete("/active")
async def deactivate_dataset(
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Deactivate the currently active dataset.
    Retains historical records in the database.
    Logs an audit event in PostgreSQL.
    """
    return deactivate_active_dataset(current_user)

