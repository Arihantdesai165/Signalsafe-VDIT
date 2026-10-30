# -*- coding: utf-8 -*-
"""
SignalSafe Campus - College Payment QR Registry & Verification Service.
Provides persistent storage, lifecycle management, canonicalization,
and layered verification of approved JCER College payment QR codes.
"""

import os
import re
import io
import json
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs, urlencode, unquote

import cv2
import numpy as np
from PIL import Image
from sqlalchemy import func, or_, desc
from fastapi import HTTPException, status, UploadFile

from ..database.connection import SessionLocal
from ..database.models import CollegePaymentQR, SecurityAuditLog
from .qrcode_service import _decode_qr_multi_pass, _parse_upi_uri, _extract_processor

logger = logging.getLogger("signalsafe.college_qr")

# Secure local storage directory for uploaded QR images
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLLEGE_QR_STORAGE_DIR = os.path.join(BASE_DIR, "data", "college_qrs")
os.makedirs(COLLEGE_QR_STORAGE_DIR, exist_ok=True)

MANDATORY_REGISTRY_NOTICE = (
    "This QR matches an active QR record approved by JCER CyberAdmin. "
    "This registry match does not independently prove bank-account ownership or confirm that a payment has occurred."
)

APPROVED_PAYMENT_PURPOSES = [
    "Tuition Fees",
    "Examination Fees",
    "Hostel & Mess Fees",
    "Library Dues & Deposits",
    "Transportation & Bus Pass",
    "Cafeteria & Meal Service",
    "Event Registration",
    "Laboratory & Course Material",
    "Sports Complex & Gym",
    "Alumni & Placement Cell",
    "Other Approved College Payment",
]

APPROVED_DEPARTMENTS = [
    "Finance & Accounts Office",
    "Examination & Evaluation Cell",
    "Hostel Administration",
    "Central Library",
    "Transportation Department",
    "Campus Cafeteria",
    "Computer Science & Engineering",
    "Electronics & Communication Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Master of Business Administration (MBA)",
    "Student Welfare & Activities Cell",
    "General College Administration",
]


# ==============================================================================
# CANONICALIZATION & FINGERPRINTING
# ==============================================================================

def canonicalize_upi_uri(uri: str) -> str:
    """
    Produces a strictly normalized, canonical representation of a UPI payment URI.
    Ensures that non-semantic variations (query parameter order, capitalization,
    trailing spaces) produce the identical payload representation.

    Rules:
    - Base URI preserved: 'upi://pay'
    - Parameter keys converted to lowercase
    - 'pa' (payee VPA) converted to lowercase and stripped
    - 'cu' (currency) converted to uppercase (e.g. 'INR')
    - 'am' (amount) formatted to 2-decimal string if valid positive float
    - 'pn' (payee name) stripped of extra internal and surrounding whitespace
    - All other query parameters stripped and preserved
    - Parameters sorted alphabetically by key
    """
    clean_uri = (uri or "").strip()
    if not (clean_uri.lower().startswith("upi://pay") or clean_uri.lower().startswith("upi://")):
        return clean_uri

    try:
        parsed = urlparse(clean_uri)
        raw_params = parse_qs(parsed.query, keep_blank_values=False)
        normalized_params: Dict[str, str] = {}

        for k, v_list in raw_params.items():
            if not v_list:
                continue
            key_clean = k.strip().lower()
            val_clean = unquote(v_list[0]).strip()

            if key_clean == "pa":
                normalized_params["pa"] = val_clean.lower()
            elif key_clean == "pn":
                normalized_params["pn"] = " ".join(val_clean.split())
            elif key_clean == "cu":
                normalized_params["cu"] = val_clean.upper() if val_clean else "INR"
            elif key_clean == "am":
                try:
                    amt_float = float(val_clean.replace(",", ""))
                    normalized_params["am"] = f"{amt_float:.2f}"
                except ValueError:
                    normalized_params["am"] = val_clean
            elif key_clean == "mc":
                normalized_params["mc"] = val_clean.upper()
            else:
                normalized_params[key_clean] = val_clean

        # Sort parameters alphabetically by key for stable representation
        sorted_items = sorted(normalized_params.items(), key=lambda item: item[0])
        canonical_query = urlencode(sorted_items)
        return f"upi://pay?{canonical_query}"

    except Exception as exc:
        logger.warning("URI canonicalization fallback: %s", exc)
        return clean_uri


def compute_payload_fingerprint(uri: str) -> str:
    """
    Calculates a stable cryptographic SHA-256 fingerprint from the canonical payload.
    Used for indexed exact lookup across thousands of approved registry records.
    """
    canonical = canonicalize_upi_uri(uri)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ==============================================================================
# IMAGE DECODING & STORAGE
# ==============================================================================

def decode_qr_image_bytes(image_bytes: bytes) -> Dict[str, Any]:
    """
    Decodes a QR code image using multi-pass computer vision techniques.
    Extracts raw payload, canonical representation, fingerprint, and payment parameters.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return {
            "success": False,
            "error": "Invalid image format. Could not decode image data.",
        }

    decoded_text, diagnostics = _decode_qr_multi_pass(img, return_diagnostics=True)
    if not decoded_text:
        return {
            "success": False,
            "error": "No decodable QR code detected in the uploaded image.",
            "diagnostics": diagnostics,
        }

    decoded_text = decoded_text.strip()
    upi_data = _parse_upi_uri(decoded_text)
    canonical = canonicalize_upi_uri(decoded_text)
    fingerprint = compute_payload_fingerprint(canonical)

    parsed_amount = None
    if upi_data.get("am"):
        try:
            parsed_amount = float(str(upi_data["am"]).replace(",", "").strip())
        except ValueError:
            parsed_amount = None

    return {
        "success": True,
        "raw_payload": decoded_text,
        "canonical_payload": canonical,
        "payload_fingerprint": fingerprint,
        "is_upi": bool(upi_data.get("is_upi")),
        "diagnostics": diagnostics,
        "extracted_fields": {
            "expected_upi_id": upi_data.get("pa", "").strip().lower(),
            "official_recipient_name": upi_data.get("pn", "").strip(),
            "expected_amount": parsed_amount,
            "currency": upi_data.get("cu", "INR").upper(),
            "merchant_code": upi_data.get("mc", "").strip(),
            "transaction_ref": upi_data.get("tr", "").strip(),
            "transaction_note": upi_data.get("tn", "").strip(),
            "processor": _extract_processor(upi_data.get("pa", "")),
            "aid": upi_data.get("aid", ""),
            "mode": upi_data.get("mode", ""),
            "purpose": upi_data.get("purpose", ""),
        },
    }


def save_qr_image_to_storage(image_bytes: bytes, filename: str) -> str:
    """
    Saves an uploaded QR image securely into the dedicated college QR directory.
    Uses uuid-based naming to prevent path traversal and collisions.
    Returns relative image storage reference.
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        ext = ".png"

    storage_ref = f"college_qr_{uuid.uuid4().hex[:16]}{ext}"
    target_path = os.path.join(COLLEGE_QR_STORAGE_DIR, storage_ref)

    with open(target_path, "wb") as f:
        f.write(image_bytes)

    return storage_ref


def get_qr_image_disk_path(storage_ref: str) -> Optional[str]:
    """
    Resolves safe path to a stored QR image, preventing path traversal attacks.
    """
    if not storage_ref:
        return None
    safe_name = os.path.basename(storage_ref)
    resolved_path = os.path.abspath(os.path.join(COLLEGE_QR_STORAGE_DIR, safe_name))
    if not resolved_path.startswith(os.path.abspath(COLLEGE_QR_STORAGE_DIR)):
        return None
    if os.path.exists(resolved_path):
        return resolved_path
    return None


# ==============================================================================
# DUPLICATE CHECKS & WARNINGS
# ==============================================================================

def check_duplicate_qr(
    fingerprint: str,
    upi_id: str,
    exclude_record_id: Optional[str] = None,
) -> List[str]:
    """
    Detects potential duplicate QR payloads or conflicting payment destinations.
    Returns advisory warning strings for administrator review.
    """
    session = SessionLocal()
    warnings = []
    try:
        # 1. Exact canonical payload duplicate
        query_exact = session.query(CollegePaymentQR).filter(
            CollegePaymentQR.payload_fingerprint == fingerprint,
            CollegePaymentQR.approval_status != "ARCHIVED",
        )
        if exclude_record_id:
            query_exact = query_exact.filter(CollegePaymentQR.record_id != exclude_record_id)

        dup_payload = query_exact.first()
        if dup_payload:
            status_text = "Active" if dup_payload.is_active else dup_payload.approval_status
            warnings.append(
                f"Identical QR payload already registered as '{dup_payload.display_name}' "
                f"({dup_payload.record_id}, Status: {status_text})."
            )

        # 2. Existing destination UPI ID check
        if upi_id:
            query_upi = session.query(CollegePaymentQR).filter(
                func.lower(CollegePaymentQR.expected_upi_id) == upi_id.lower().strip(),
                CollegePaymentQR.approval_status != "ARCHIVED",
            )
            if exclude_record_id:
                query_upi = query_upi.filter(CollegePaymentQR.record_id != exclude_record_id)

            dup_upi = query_upi.first()
            if dup_upi and not dup_payload:
                warnings.append(
                    f"Payment destination UPI ID '{upi_id}' is already registered under "
                    f"'{dup_upi.display_name}' ({dup_upi.record_id}). Verify if this is an intended separate counter."
                )

        return warnings
    finally:
        session.close()


# ==============================================================================
# CYBERADMIN REGISTRY MANAGEMENT (CRUD & LIFECYCLE)
# ==============================================================================

def register_college_qr(
    image_bytes: bytes,
    filename: str,
    display_name: str,
    payment_purpose: str,
    official_recipient_name: str,
    expected_upi_id: str,
    department: Optional[str] = None,
    expected_amount: Optional[float] = None,
    description: Optional[str] = None,
    admin_user: Dict[str, Any] = None,
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """
    Registers a new official JCER College payment QR code.
    Decodes the QR image, canonicalizes the payload, stores the image securely,
    and records the registry entry in PostgreSQL.
    """
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    # Decode QR image
    decoded_info = decode_qr_image_bytes(image_bytes)
    if not decoded_info["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"QR Decoding Error: {decoded_info['error']}",
        )

    raw_payload = decoded_info["raw_payload"]
    fingerprint = decoded_info["payload_fingerprint"]
    extracted = decoded_info["extracted_fields"]

    # Use decoded values as fallbacks if user left them empty
    final_upi_id = (expected_upi_id or extracted.get("expected_upi_id") or "").strip().lower()
    final_recipient = (official_recipient_name or extracted.get("official_recipient_name") or "Jain College of Engineering & Research").strip()
    final_amount = expected_amount if expected_amount is not None else extracted.get("expected_amount")
    final_currency = extracted.get("currency") or "INR"
    final_merchant_code = extracted.get("merchant_code") or ""

    if not final_upi_id or "@" not in final_upi_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid expected UPI ID (@handle) is required.",
        )

    # Save image securely
    storage_ref = save_qr_image_to_storage(image_bytes, filename)

    # Generate record ID
    record_id = f"JCER-QR-{uuid.uuid4().hex[:10].upper()}"

    approval_status = "APPROVED" if auto_approve else "PENDING_APPROVAL"
    is_active = True if auto_approve else False

    session = SessionLocal()
    try:
        new_qr = CollegePaymentQR(
            record_id=record_id,
            display_name=display_name.strip(),
            payment_purpose=payment_purpose.strip(),
            department=department.strip() if department else None,
            official_recipient_name=final_recipient,
            expected_upi_id=final_upi_id,
            expected_amount=final_amount,
            currency=final_currency,
            merchant_code=final_merchant_code,
            qr_payload=raw_payload,
            payload_fingerprint=fingerprint,
            image_storage_ref=storage_ref,
            approval_status=approval_status,
            is_active=is_active,
            created_by_erp_id=admin_erp_id,
            created_by_name=admin_name,
            approved_by_erp_id=admin_erp_id if auto_approve else None,
            approved_by_name=admin_name if auto_approve else None,
            description=description.strip() if description else None,
            created_at=now_utc,
            updated_at=now_utc,
            approved_at=now_utc if auto_approve else None,
        )
        session.add(new_qr)

        # Audit Log
        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_REGISTERED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps({
                "display_name": display_name,
                "purpose": payment_purpose,
                "upi_id": final_upi_id,
                "approval_status": approval_status,
                "is_active": is_active,
            }),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return _serialize_college_qr(new_qr)

    except Exception as exc:
        session.rollback()
        logger.error("Failed to register college QR: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error registering college QR: {str(exc)}",
        )
    finally:
        session.close()


def bulk_register_college_qrs(
    files: List[Tuple[str, bytes]],
    admin_user: Dict[str, Any],
    default_purpose: str = "Tuition Fees",
    default_department: Optional[str] = "Finance & Accounts Office",
    auto_approve: bool = False,
) -> Dict[str, Any]:
    """
    Processes multiple QR code images in a batch.
    Per-file error isolation ensures that an unreadable file does not fail the batch.
    """
    total = len(files)
    successful = []
    failed = []

    for filename, file_bytes in files:
        try:
            # Decode image
            dec = decode_qr_image_bytes(file_bytes)
            if not dec["success"]:
                failed.append({
                    "filename": filename,
                    "reason": dec["error"],
                })
                continue

            extracted = dec["extracted_fields"]
            upi_id = extracted.get("expected_upi_id")
            if not upi_id:
                failed.append({
                    "filename": filename,
                    "reason": "Decoded QR does not contain a UPI payment destination (missing 'pa').",
                })
                continue

            # Derive display name from filename
            clean_name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
            if not clean_name:
                clean_name = f"JCER QR {extracted.get('official_recipient_name') or upi_id}"

            rec = register_college_qr(
                image_bytes=file_bytes,
                filename=filename,
                display_name=clean_name,
                payment_purpose=default_purpose,
                official_recipient_name=extracted.get("official_recipient_name") or "Jain College of Engineering & Research",
                expected_upi_id=upi_id,
                department=default_department,
                expected_amount=extracted.get("expected_amount"),
                description=f"Bulk imported from {filename}",
                admin_user=admin_user,
                auto_approve=auto_approve,
            )
            successful.append({
                "filename": filename,
                "record_id": rec["record_id"],
                "display_name": rec["display_name"],
                "upi_id": rec["expected_upi_id"],
                "is_active": rec["is_active"],
            })

        except Exception as exc:
            failed.append({
                "filename": filename,
                "reason": str(exc),
            })

    return {
        "total_files": total,
        "processed": len(successful) + len(failed),
        "successful_count": len(successful),
        "failed_count": len(failed),
        "successful": successful,
        "failed": failed,
    }


def approve_and_activate_qr(record_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Explicitly approves and activates a college QR code record."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")

        record.approval_status = "APPROVED"
        record.is_active = True
        record.approved_at = now_utc
        record.approved_by_erp_id = admin_erp_id
        record.approved_by_name = admin_name
        record.updated_at = now_utc

        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-APP-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_APPROVED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps({"display_name": record.display_name, "upi_id": record.expected_upi_id}),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return {
            "success": True,
            "message": f"QR Record '{record.display_name}' ({record.record_id}) has been approved and activated.",
            "record": _serialize_college_qr(record),
        }
    finally:
        session.close()


def deactivate_qr(record_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Deactivates an approved QR code record without deleting historical data."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")

        record.is_active = False
        record.deactivated_at = now_utc
        record.updated_at = now_utc

        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-DEACT-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_DEACTIVATED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps({"display_name": record.display_name}),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return {
            "success": True,
            "message": f"QR Record '{record.display_name}' has been deactivated.",
            "record": _serialize_college_qr(record),
        }
    finally:
        session.close()


def reactivate_qr(record_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Reactivates an approved but previously deactivated QR code record."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")

        record.is_active = True
        record.deactivated_at = None
        record.updated_at = now_utc

        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-REACT-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_REACTIVATED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps({"display_name": record.display_name}),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return {
            "success": True,
            "message": f"QR Record '{record.display_name}' has been reactivated.",
            "record": _serialize_college_qr(record),
        }
    finally:
        session.close()


def update_qr_metadata(record_id: str, update_data: Dict[str, Any], admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Updates metadata fields of an existing QR record."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")

        if "display_name" in update_data and update_data["display_name"]:
            record.display_name = update_data["display_name"].strip()
        if "payment_purpose" in update_data and update_data["payment_purpose"]:
            record.payment_purpose = update_data["payment_purpose"].strip()
        if "department" in update_data:
            record.department = update_data["department"].strip() if update_data["department"] else None
        if "official_recipient_name" in update_data and update_data["official_recipient_name"]:
            record.official_recipient_name = update_data["official_recipient_name"].strip()
        if "description" in update_data:
            record.description = update_data["description"].strip() if update_data["description"] else None
        if "expected_amount" in update_data:
            raw_amt = update_data["expected_amount"]
            if raw_amt is not None and str(raw_amt).strip() != "":
                try:
                    record.expected_amount = float(str(raw_amt).replace(",", "").strip())
                except ValueError:
                    pass
            else:
                record.expected_amount = None

        record.updated_at = now_utc

        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-UPD-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_METADATA_UPDATED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps(update_data),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return {
            "success": True,
            "message": f"QR Record '{record.display_name}' metadata updated successfully.",
            "record": _serialize_college_qr(record),
        }
    finally:
        session.close()


def replace_qr_image(record_id: str, new_image_bytes: bytes, filename: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Replaces the QR image and re-decodes the payload for an existing record."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    dec = decode_qr_image_bytes(new_image_bytes)
    if not dec["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Replacement image error: {dec['error']}",
        )

    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")

        # Save new image
        new_storage_ref = save_qr_image_to_storage(new_image_bytes, filename)

        # Update record
        record.qr_payload = dec["raw_payload"]
        record.payload_fingerprint = dec["payload_fingerprint"]
        record.image_storage_ref = new_storage_ref
        record.updated_at = now_utc

        extracted = dec["extracted_fields"]
        if extracted.get("expected_upi_id"):
            record.expected_upi_id = extracted["expected_upi_id"]
        if extracted.get("official_recipient_name"):
            record.official_recipient_name = extracted["official_recipient_name"]
        if extracted.get("expected_amount") is not None:
            record.expected_amount = extracted["expected_amount"]

        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-REPL-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_IMAGE_REPLACED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps({"new_fingerprint": dec["payload_fingerprint"], "filename": filename}),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return {
            "success": True,
            "message": f"QR Image replaced and re-decoded successfully for '{record.display_name}'.",
            "record": _serialize_college_qr(record),
        }
    finally:
        session.close()


def archive_qr(record_id: str, admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Archives a record with confirmation, preserving audit and scan references."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "CYBERADMIN")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter_by(record_id=record_id).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")

        record.approval_status = "ARCHIVED"
        record.is_active = False
        record.archived_at = now_utc
        record.updated_at = now_utc

        audit_log = SecurityAuditLog(
            event_id=f"AUD-QR-ARCH-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="COLLEGE_QR_ARCHIVED",
            target_resource_type="college_payment_qr",
            target_resource_id=record_id,
            outcome="SUCCESS",
            details=json.dumps({"display_name": record.display_name}),
            created_at=now_utc,
        )
        session.add(audit_log)
        session.commit()

        return {
            "success": True,
            "message": f"QR Record '{record.display_name}' has been archived.",
        }
    finally:
        session.close()


def get_college_qr_record(record_id: str) -> Dict[str, Any]:
    """Retrieves a single college QR record by record_id."""
    session = SessionLocal()
    try:
        record = session.query(CollegePaymentQR).filter(
            or_(CollegePaymentQR.record_id == record_id, CollegePaymentQR.id == (int(record_id) if record_id.isdigit() else -1))
        ).first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR record not found.")
        return _serialize_college_qr(record)
    finally:
        session.close()


def list_college_qrs(
    search: Optional[str] = None,
    payment_purpose: Optional[str] = None,
    department: Optional[str] = None,
    approval_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 15,
) -> Dict[str, Any]:
    """
    Search, filter, and paginate the college QR registry.
    Scales efficiently across thousands of records.
    """
    session = SessionLocal()
    try:
        query = session.query(CollegePaymentQR)

        if search:
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    func.lower(CollegePaymentQR.display_name).like(term),
                    func.lower(CollegePaymentQR.expected_upi_id).like(term),
                    func.lower(CollegePaymentQR.official_recipient_name).like(term),
                    func.lower(CollegePaymentQR.record_id).like(term),
                )
            )

        if payment_purpose and payment_purpose != "ALL":
            query = query.filter(CollegePaymentQR.payment_purpose == payment_purpose)

        if department and department != "ALL":
            query = query.filter(CollegePaymentQR.department == department)

        if approval_status and approval_status != "ALL":
            query = query.filter(CollegePaymentQR.approval_status == approval_status)
        else:
            # Default: hide archived unless explicitly asked
            query = query.filter(CollegePaymentQR.approval_status != "ARCHIVED")

        if is_active is not None:
            query = query.filter(CollegePaymentQR.is_active == is_active)

        total_count = query.count()
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        offset = (page - 1) * page_size

        records = query.order_by(desc(CollegePaymentQR.created_at)).offset(offset).limit(page_size).all()

        return {
            "records": [_serialize_college_qr(r) for r in records],
            "total_count": total_count,
            "total_pages": total_pages,
            "page": page,
            "page_size": page_size,
        }
    finally:
        session.close()


def get_registry_stats() -> Dict[str, Any]:
    """
    Retrieves real-time database counts for the College QR Registry.
    """
    session = SessionLocal()
    try:
        total = session.query(CollegePaymentQR).filter(CollegePaymentQR.approval_status != "ARCHIVED").count()
        active = session.query(CollegePaymentQR).filter_by(is_active=True, approval_status="APPROVED").count()
        inactive = session.query(CollegePaymentQR).filter_by(is_active=False).filter(CollegePaymentQR.approval_status != "ARCHIVED").count()
        pending = session.query(CollegePaymentQR).filter_by(approval_status="PENDING_APPROVAL").count()
        archived = session.query(CollegePaymentQR).filter_by(approval_status="ARCHIVED").count()

        dept_count = session.query(func.count(func.distinct(CollegePaymentQR.department))).scalar() or 0
        purpose_count = session.query(func.count(func.distinct(CollegePaymentQR.payment_purpose))).scalar() or 0

        return {
            "total_registered": total,
            "active_approved": active,
            "inactive": inactive,
            "awaiting_approval": pending,
            "archived": archived,
            "departments_count": dept_count,
            "purposes_count": purpose_count,
            "configured_purposes": APPROVED_PAYMENT_PURPOSES,
            "configured_departments": APPROVED_DEPARTMENTS,
            "registry_notice": MANDATORY_REGISTRY_NOTICE,
        }
    finally:
        session.close()


def _serialize_college_qr(qr: CollegePaymentQR) -> Dict[str, Any]:
    """Serializes a CollegePaymentQR model instance safely without internal path leaks."""
    return {
        "id": qr.id,
        "record_id": qr.record_id,
        "display_name": qr.display_name,
        "payment_purpose": qr.payment_purpose,
        "department": qr.department,
        "official_recipient_name": qr.official_recipient_name,
        "expected_upi_id": qr.expected_upi_id,
        "expected_amount": qr.expected_amount,
        "currency": qr.currency,
        "merchant_code": qr.merchant_code,
        "qr_payload": qr.qr_payload,
        "payload_fingerprint": qr.payload_fingerprint,
        "has_image": bool(qr.image_storage_ref),
        "approval_status": qr.approval_status,
        "is_active": qr.is_active,
        "created_by": qr.created_by_name or qr.created_by_erp_id or "CyberAdmin",
        "approved_by": qr.approved_by_name or qr.approved_by_erp_id,
        "description": qr.description,
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
        "updated_at": qr.updated_at.isoformat() if qr.updated_at else None,
        "approved_at": qr.approved_at.isoformat() if qr.approved_at else None,
        "deactivated_at": qr.deactivated_at.isoformat() if qr.deactivated_at else None,
        "archived_at": qr.archived_at.isoformat() if qr.archived_at else None,
    }


# ==============================================================================
# LAYERED QR VERIFICATION MATCHING ENGINE
# ==============================================================================

def match_qr_against_college_registry(
    decoded_text: str,
    upi_data: Dict[str, Any],
    existing_security_findings: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executes layered comparison against active, approved college QR records.
    Never overrides serious security findings (Layer 6).

    Classifications:
    - VERIFIED_JCER_COLLEGE_QR
    - KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER
    - OTHER_UPI_QR_NOT_REGISTERED
    - SUSPICIOUS_OR_UNSAFE_QR
    - UNABLE_TO_VERIFY
    - NO_ACTIVE_COLLEGE_REGISTRY
    """
    # -------------------------------------------------------------
    # Layer 6 Check: Critical threat identified by base security checks
    # -------------------------------------------------------------
    base_risk = existing_security_findings.get("risk_score", 0)
    base_reasons = existing_security_findings.get("reasons", [])
    is_critical_threat = (
        base_risk >= 80 or
        any("phishing" in r.lower() or "block" in r.lower() or "scam" in r.lower() for r in base_reasons)
    )

    if not decoded_text or not upi_data.get("is_upi"):
        # Layer 6 / 7 for non-UPI content
        if decoded_text and decoded_text.startswith("http"):
            return {
                "classification": "SUSPICIOUS_OR_UNSAFE_QR",
                "heading": "Suspicious or Unsafe QR Code",
                "explanation": (
                    "QR code contains an external web URL instead of a legitimate UPI payment address. "
                    "This pattern is commonly used in phishing campaigns."
                ),
                "is_college_verified": False,
                "registry_match": None,
                "matched_fields": [],
                "differing_fields": [],
                "security_findings": base_reasons,
                "registry_notice": MANDATORY_REGISTRY_NOTICE,
            }

        return {
            "classification": "UNABLE_TO_VERIFY",
            "heading": "Unable to Verify QR Code",
            "explanation": "Image does not contain a decodable UPI payment QR code.",
            "is_college_verified": False,
            "registry_match": None,
            "matched_fields": [],
            "differing_fields": [],
            "security_findings": base_reasons,
            "registry_notice": MANDATORY_REGISTRY_NOTICE,
        }

    # Extract observed fields
    obs_pa = (upi_data.get("pa") or "").strip().lower()
    obs_pn = (upi_data.get("pn") or "").strip()
    obs_am = None
    if upi_data.get("am"):
        try:
            obs_am = float(str(upi_data["am"]).replace(",", "").strip())
        except ValueError:
            obs_am = None
    obs_cu = (upi_data.get("cu") or "INR").strip().upper()
    obs_mc = (upi_data.get("mc") or "").strip()

    fingerprint = compute_payload_fingerprint(decoded_text)

    session = SessionLocal()
    try:
        # Check active registry availability
        active_count = session.query(CollegePaymentQR).filter_by(
            is_active=True, approval_status="APPROVED"
        ).count()

        if active_count == 0:
            return {
                "classification": "NO_ACTIVE_COLLEGE_REGISTRY",
                "heading": "College QR Registry Inactive",
                "explanation": (
                    "No approved college payment QR records are currently active in the JCER registry. "
                    "College-specific payment verification is temporarily unavailable."
                ),
                "is_college_verified": False,
                "registry_match": None,
                "matched_fields": [],
                "differing_fields": [],
                "security_findings": base_reasons,
                "registry_notice": MANDATORY_REGISTRY_NOTICE,
            }

        # -------------------------------------------------------------
        # Layer 2: Exact registered-payload comparison via canonical fingerprint
        # -------------------------------------------------------------
        exact_record: Optional[CollegePaymentQR] = (
            session.query(CollegePaymentQR)
            .filter_by(payload_fingerprint=fingerprint, is_active=True, approval_status="APPROVED")
            .first()
        )

        if exact_record:
            # If base security checks detected a critical threat, preserve it!
            if is_critical_threat:
                return {
                    "classification": "SUSPICIOUS_OR_UNSAFE_QR",
                    "heading": "Suspicious or Unsafe QR Content",
                    "explanation": (
                        f"Warning: Although the payload references registered record '{exact_record.display_name}', "
                        "critical security anomalies were detected in the QR structure."
                    ),
                    "is_college_verified": False,
                    "registry_match": _serialize_college_qr(exact_record),
                    "matched_fields": ["Exact Payload Match"],
                    "differing_fields": [],
                    "security_findings": base_reasons,
                    "registry_notice": MANDATORY_REGISTRY_NOTICE,
                }

            matched_fields_list = [
                {"field": "Payment Destination (UPI ID)", "observed": obs_pa, "expected": exact_record.expected_upi_id, "matched": True},
                {"field": "Payee Name", "observed": obs_pn, "expected": exact_record.official_recipient_name, "matched": True},
                {"field": "Currency", "observed": obs_cu, "expected": exact_record.currency, "matched": True},
            ]
            if exact_record.expected_amount is not None and obs_am is not None:
                matched_fields_list.append({
                    "field": "Amount", "observed": f"₹{obs_am:.2f}", "expected": f"₹{exact_record.expected_amount:.2f}", "matched": True
                })

            return {
                "classification": "VERIFIED_JCER_COLLEGE_QR",
                "heading": "Verified JCER College QR",
                "explanation": (
                    f"This QR matches an active QR record approved by JCER CyberAdmin for '{exact_record.display_name}'. "
                    f"{MANDATORY_REGISTRY_NOTICE}"
                ),
                "is_college_verified": True,
                "registered_display_name": exact_record.display_name,
                "payment_purpose": exact_record.payment_purpose,
                "department": exact_record.department,
                "official_recipient_name": exact_record.official_recipient_name,
                "expected_upi_id": exact_record.expected_upi_id,
                "expected_amount": exact_record.expected_amount,
                "registry_match": _serialize_college_qr(exact_record),
                "matched_fields": matched_fields_list,
                "differing_fields": [],
                "security_findings": base_reasons,
                "registry_notice": MANDATORY_REGISTRY_NOTICE,
            }

        # -------------------------------------------------------------
        # Layer 3 & 4: Field-level comparison (Known Destination with Differences)
        # -------------------------------------------------------------
        candidate_record: Optional[CollegePaymentQR] = None
        if obs_pa:
            candidate_record = (
                session.query(CollegePaymentQR)
                .filter(
                    func.lower(CollegePaymentQR.expected_upi_id) == obs_pa.lower(),
                    CollegePaymentQR.is_active == True,
                    CollegePaymentQR.approval_status == "APPROVED",
                )
                .first()
            )

        if candidate_record:
            matched_fields_list = [
                {"field": "Payment Destination (UPI ID)", "observed": obs_pa, "expected": candidate_record.expected_upi_id, "matched": True}
            ]
            differing_fields_list = []

            # Check Payee Name
            norm_obs_pn = " ".join(obs_pn.lower().split())
            norm_exp_pn = " ".join(candidate_record.official_recipient_name.lower().split())
            if norm_obs_pn and norm_exp_pn:
                pn_match = (norm_obs_pn in norm_exp_pn) or (norm_exp_pn in norm_obs_pn)
                if pn_match:
                    matched_fields_list.append({
                        "field": "Official Recipient Name",
                        "observed": obs_pn,
                        "expected": candidate_record.official_recipient_name,
                        "matched": True,
                    })
                else:
                    differing_fields_list.append({
                        "field": "Official Recipient Name",
                        "observed": obs_pn,
                        "expected": candidate_record.official_recipient_name,
                        "description": f"Payee name in QR '{obs_pn}' differs from registered '{candidate_record.official_recipient_name}'.",
                    })

            # Check Amount
            if candidate_record.expected_amount is not None:
                if obs_am is not None:
                    if abs(obs_am - candidate_record.expected_amount) < 0.05:
                        matched_fields_list.append({
                            "field": "Amount",
                            "observed": f"₹{obs_am:.2f}",
                            "expected": f"₹{candidate_record.expected_amount:.2f}",
                            "matched": True,
                        })
                    else:
                        differing_fields_list.append({
                            "field": "Amount",
                            "observed": obs_am,
                            "expected": candidate_record.expected_amount,
                            "description": f"QR specifies ₹{obs_am:.2f}, while registered fee is ₹{candidate_record.expected_amount:.2f}.",
                        })
                else:
                    differing_fields_list.append({
                        "field": "Amount",
                        "observed": "Variable / None",
                        "expected": candidate_record.expected_amount,
                        "description": f"Registered record expects fixed amount ₹{candidate_record.expected_amount:.2f}.",
                    })

            # Check Merchant Code if specified
            if candidate_record.merchant_code and obs_mc:
                if candidate_record.merchant_code.upper() == obs_mc.upper():
                    matched_fields_list.append({
                        "field": "Merchant Category Code", "observed": obs_mc, "expected": candidate_record.merchant_code, "matched": True
                    })
                else:
                    differing_fields_list.append({
                        "field": "Merchant Category Code",
                        "observed": obs_mc,
                        "expected": candidate_record.merchant_code,
                        "description": f"Merchant code '{obs_mc}' differs from registered '{candidate_record.merchant_code}'.",
                    })

            if differing_fields_list:
                return {
                    "classification": "KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER",
                    "heading": "Known College Recipient — QR Details Differ",
                    "explanation": (
                        f"Payment destination '{obs_pa}' matches registered college counter '{candidate_record.display_name}', "
                        f"but {len(differing_fields_list)} field(s) differ from the approved record."
                    ),
                    "is_college_verified": False,
                    "registered_display_name": candidate_record.display_name,
                    "payment_purpose": candidate_record.payment_purpose,
                    "department": candidate_record.department,
                    "official_recipient_name": candidate_record.official_recipient_name,
                    "expected_upi_id": candidate_record.expected_upi_id,
                    "registry_match": _serialize_college_qr(candidate_record),
                    "matched_fields": matched_fields_list,
                    "differing_fields": differing_fields_list,
                    "security_findings": base_reasons,
                    "registry_notice": MANDATORY_REGISTRY_NOTICE,
                }

            # All available fields agreed even if canonical payload had non-semantic extra parameters
            return {
                "classification": "VERIFIED_JCER_COLLEGE_QR",
                "heading": "Verified JCER College QR",
                "explanation": (
                    f"This QR destination and payee details match approved college record '{candidate_record.display_name}'. "
                    f"{MANDATORY_REGISTRY_NOTICE}"
                ),
                "is_college_verified": True,
                "registered_display_name": candidate_record.display_name,
                "payment_purpose": candidate_record.payment_purpose,
                "department": candidate_record.department,
                "official_recipient_name": candidate_record.official_recipient_name,
                "expected_upi_id": candidate_record.expected_upi_id,
                "registry_match": _serialize_college_qr(candidate_record),
                "matched_fields": matched_fields_list,
                "differing_fields": [],
                "security_findings": base_reasons,
                "registry_notice": MANDATORY_REGISTRY_NOTICE,
            }

        # -------------------------------------------------------------
        # Layer 5: Other UPI QR - Not Registered by JCER
        # -------------------------------------------------------------
        return {
            "classification": "OTHER_UPI_QR_NOT_REGISTERED",
            "heading": "Other UPI QR — Not Registered by JCER",
            "explanation": (
                "UPI payment information was detected, but this QR does not match an approved JCER college QR record. "
                "The college registry cannot confirm its relationship to JCER."
            ),
            "is_college_verified": False,
            "registry_match": None,
            "matched_fields": [],
            "differing_fields": [],
            "security_findings": base_reasons,
            "registry_notice": MANDATORY_REGISTRY_NOTICE,
        }

    finally:
        session.close()
