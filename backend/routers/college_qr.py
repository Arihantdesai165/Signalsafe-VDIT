# -*- coding: utf-8 -*-
"""
SignalSafe Campus - CyberAdmin College Payment QR Registry Router.
Provides administrative endpoints to register, decode, review, approve,
edit, replace, activate, deactivate, and archive official JCER College payment QRs.
All endpoints require authenticated CyberAdmin role.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any, List

from ..services.auth_service import require_cyberadmin
from ..services.college_qr_service import (
    decode_qr_image_bytes,
    check_duplicate_qr,
    register_college_qr,
    bulk_register_college_qrs,
    approve_and_activate_qr,
    deactivate_qr,
    reactivate_qr,
    update_qr_metadata,
    replace_qr_image,
    archive_qr,
    get_college_qr_record,
    list_college_qrs,
    get_registry_stats,
    get_qr_image_disk_path,
    MANDATORY_REGISTRY_NOTICE,
)

router = APIRouter(prefix="/api/cyberadmin/college-qr", tags=["CyberAdmin College QR Registry"])

MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB limit


@router.get("/stats")
async def get_stats(
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Retrieve real database statistics for the College Payment QR Registry.
    Requires CyberAdmin role.
    """
    return get_registry_stats()


@router.get("")
async def list_qrs(
    search: Optional[str] = Query(None),
    payment_purpose: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    approval_status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(15, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Search, filter, and paginate through the College Payment QR Registry.
    Requires CyberAdmin role.
    """
    return list_college_qrs(
        search=search,
        payment_purpose=payment_purpose,
        department=department,
        approval_status=approval_status,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.post("/decode-preview")
@router.post("/preview-decode")
async def preview_qr_decode(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Decodes an uploaded QR image without persisting it.
    Extracts raw payload, canonical representation, fingerprint, and payment fields.
    Checks for duplicate payloads or destinations in the existing registry.
    """
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 10 MB size limit.")

    dec = decode_qr_image_bytes(image_bytes)
    if not dec["success"]:
        return {
            "success": False,
            "error": dec["error"],
        }

    # Duplicate check
    warnings = check_duplicate_qr(
        fingerprint=dec["payload_fingerprint"],
        upi_id=dec["extracted_fields"].get("expected_upi_id", ""),
    )

    return {
        "success": True,
        "raw_payload": dec["raw_payload"],
        "canonical_payload": dec["canonical_payload"],
        "payload_fingerprint": dec["payload_fingerprint"],
        "is_upi": dec["is_upi"],
        "extracted_fields": dec["extracted_fields"],
        "warnings": warnings,
        "diagnostics": dec.get("diagnostics"),
    }


@router.post("")
@router.post("/upload")
async def create_college_qr(
    file: UploadFile = File(...),
    display_name: str = Form(...),
    payment_purpose: str = Form(...),
    official_recipient_name: str = Form(...),
    expected_upi_id: str = Form(...),
    department: Optional[str] = Form(None),
    expected_amount: Optional[float] = Form(None),
    description: Optional[str] = Form(None),
    auto_approve: bool = Form(False),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Register a new official JCER College payment QR code.
    Requires CyberAdmin role.
    """
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 10 MB size limit.")

    record = register_college_qr(
        image_bytes=image_bytes,
        filename=file.filename or "college_qr.png",
        display_name=display_name,
        payment_purpose=payment_purpose,
        official_recipient_name=official_recipient_name,
        expected_upi_id=expected_upi_id,
        department=department,
        expected_amount=expected_amount,
        description=description,
        admin_user=current_user,
        auto_approve=auto_approve,
    )
    return {
        "success": True,
        "message": f"College QR record '{record['display_name']}' created successfully.",
        "record": record,
    }


@router.post("/bulk")
async def bulk_upload_qrs(
    files: List[UploadFile] = File(...),
    default_purpose: str = Form("Tuition Fees"),
    default_department: Optional[str] = Form("Finance & Accounts Office"),
    auto_approve: bool = Form(False),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Upload and decode multiple college payment QR images in a batch.
    Per-file failure isolation ensures one unreadable image does not fail the batch.
    """
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided.")

    file_payloads: List[Tuple[str, bytes]] = []
    for f in files:
        content = await f.read()
        file_payloads.append((f.filename or "qr.png", content))

    summary = bulk_register_college_qrs(
        files=file_payloads,
        admin_user=current_user,
        default_purpose=default_purpose,
        default_department=default_department,
        auto_approve=auto_approve,
    )
    return summary


@router.get("/{record_id}")
async def get_qr(
    record_id: str,
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Retrieve details for a single college payment QR record."""
    return get_college_qr_record(record_id)


@router.get("/{record_id}/image")
async def get_qr_image(
    record_id: str,
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Securely serve the uploaded QR image file without exposing internal filesystem paths."""
    rec = get_college_qr_record(record_id)
    # Fetch record from database to get image_storage_ref
    from ..database.connection import SessionLocal
    from ..database.models import CollegePaymentQR
    session = SessionLocal()
    try:
        qr = session.query(CollegePaymentQR).filter_by(record_id=rec["record_id"]).first()
        if not qr or not qr.image_storage_ref:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found for this QR record.")
        disk_path = get_qr_image_disk_path(qr.image_storage_ref)
        if not disk_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found on disk.")
        return FileResponse(disk_path)
    finally:
        session.close()


@router.patch("/{record_id}")
async def update_qr(
    record_id: str,
    body: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Update metadata for an existing college QR record."""
    return update_qr_metadata(record_id, body, current_user)


@router.post("/{record_id}/replace-image")
async def replace_image(
    record_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Replace the QR image and re-decode payload for an existing record."""
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    return replace_qr_image(record_id, image_bytes, file.filename or "new_qr.png", current_user)


@router.post("/{record_id}/approve")
@router.post("/{record_id}/activate")
async def approve_qr(
    record_id: str,
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Explicitly approve and activate a college QR code record."""
    return approve_and_activate_qr(record_id, current_user)


@router.post("/{record_id}/deactivate")
async def deactivate_record(
    record_id: str,
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Deactivate an approved QR code record."""
    return deactivate_qr(record_id, current_user)


@router.post("/{record_id}/reactivate")
async def reactivate_record(
    record_id: str,
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Reactivate a previously deactivated college QR record."""
    return reactivate_qr(record_id, current_user)


@router.post("/{record_id}/archive")
async def archive_record(
    record_id: str,
    current_user: Dict[str, Any] = Depends(require_cyberadmin),
):
    """Archive a QR record while preserving historical scan and audit references."""
    return archive_qr(record_id, current_user)
