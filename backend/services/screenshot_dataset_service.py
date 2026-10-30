# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Screenshot Dataset Management & Reference Matching Service
Manages CyberAdmin CSV upload, validation, preview, atomic replacement, deactivation,
and dataset-driven reference matching for payment screenshots.

Distinguishes demonstration dataset matching from actual bank payment verification.
Mandatory notice: 'DEMO DATA — NOT BANK VERIFIED'.
"""

import re
import csv
import io
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database.connection import SessionLocal
from ..database.models import (
    ScreenshotDataset,
    ScreenshotTransactionRecord,
    SecurityAuditLog,
)

logger = logging.getLogger("signalsafe.screenshot_dataset")

EXPECTED_CSV_COLUMNS = [
    "record_id",
    "transaction_id",
    "utr_rrn",
    "transaction_date",
    "transaction_time",
    "amount_inr",
    "currency",
    "payer_display_name",
    "payer_account_masked",
    "payee_name",
    "payee_vpa",
    "bank_or_app_label",
    "transaction_status",
    "dataset_type",
    "verification_status",
    "notes",
]

MANDATORY_DEMO_NOTICE = "DEMO DATA — NOT BANK VERIFIED"


def _sanitize_cell_text(val: Any) -> str:
    """Strips dangerous formula injection characters and trims whitespace."""
    if val is None:
        return ""
    s = str(val).strip()
    # Formula injection prevention for Excel/spreadsheets
    if s.startswith(("=", "+", "-", "@")):
        s = "'" + s
    return s


def _normalize_string(val: Optional[str]) -> str:
    if not val:
        return ""
    # Lowercase, strip punctuation and repeated whitespace
    s = re.sub(r"[^\w\s@\.]", " ", str(val).lower())
    return " ".join(s.split())


def _normalize_date_str(val: Optional[str]) -> Optional[str]:
    """Normalizes dates like '11 May 2026', '11-05-2026', '2026-05-11' to YYYY-MM-DD."""
    if not val:
        return None
    s = str(val).strip()
    # Try various formats
    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d %b %y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Try extracting day, month word, year
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{2,4})", s)
    if m:
        try:
            day, mon, yr = m.group(1), m.group(2)[:3], m.group(3)
            if len(yr) == 2:
                yr = "20" + yr
            dt = datetime.strptime(f"{day} {mon} {yr}", "%d %b %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def validate_csv_content(
    file_bytes_or_text: Union[bytes, str],
    filename: str = "dataset.csv",
) -> Dict[str, Any]:
    """
    Validates CSV headers, row data types, missing required fields, and duplicate references.
    Does not modify database state.
    """
    if isinstance(file_bytes_or_text, bytes):
        try:
            text_content = file_bytes_or_text.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text_content = file_bytes_or_text.decode("latin-1")
            except Exception as e:
                return {
                    "is_valid": False,
                    "error": f"Failed to decode CSV text: {str(e)}",
                    "total_rows": 0,
                    "valid_rows": [],
                    "invalid_rows": [],
                    "duplicate_count": 0,
                    "warnings": ["File encoding could not be determined. Please save file as UTF-8."],
                }
    else:
        text_content = file_bytes_or_text

    reader = csv.DictReader(io.StringIO(text_content))
    if not reader.fieldnames:
        return {
            "is_valid": False,
            "error": "CSV file is empty or missing headers.",
            "total_rows": 0,
            "valid_rows": [],
            "invalid_rows": [],
            "duplicate_count": 0,
            "warnings": [],
        }

    # Normalize header names (lowercase, strip whitespace)
    fieldnames_clean = [f.strip().lower() for f in reader.fieldnames if f]
    missing_columns = [
        col for col in EXPECTED_CSV_COLUMNS if col.lower() not in fieldnames_clean
    ]

    warnings = []
    if missing_columns:
        warnings.append(f"Missing recommended columns: {', '.join(missing_columns)}")

    # Check minimum required identification columns
    core_columns = ["transaction_id", "utr_rrn", "amount_inr", "payee_name"]
    for core in core_columns:
        if core not in fieldnames_clean:
            return {
                "is_valid": False,
                "error": f"Required column '{core}' is missing from CSV header.",
                "total_rows": 0,
                "valid_rows": [],
                "invalid_rows": [],
                "duplicate_count": 0,
                "warnings": warnings,
            }

    valid_records = []
    invalid_rows = []
    seen_record_ids = set()
    seen_txns = set()
    seen_utrs = set()
    duplicate_count = 0

    row_index = 0
    # Map header fields
    header_map = {f.strip().lower(): f for f in reader.fieldnames if f}

    for row in reader:
        row_index += 1
        # Extract row values using header map
        rec_id = (row.get(header_map.get("record_id", "")) or f"REC-{row_index:03d}").strip()
        txn_id = (row.get(header_map.get("transaction_id", "")) or "").strip()
        utr_rrn = (row.get(header_map.get("utr_rrn", "")) or "").strip()
        amount_raw = (row.get(header_map.get("amount_inr", "")) or "").strip().replace(",", "")
        payee_name = (row.get(header_map.get("payee_name", "")) or "").strip()
        payee_vpa = (row.get(header_map.get("payee_vpa", "")) or "").strip()

        # Validation rules:
        # 1. At least one identifier must be present
        if not txn_id and not utr_rrn:
            invalid_rows.append({
                "row_index": row_index,
                "reason": "Both transaction_id and utr_rrn are empty.",
                "raw_data": row,
            })
            continue

        # 2. Amount must be a valid positive float
        try:
            amt_float = float(amount_raw)
            if amt_float <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            invalid_rows.append({
                "row_index": row_index,
                "reason": f"Invalid amount value: '{amount_raw}'. Must be positive number.",
                "raw_data": row,
            })
            continue

        # 3. Payee name must be provided
        if not payee_name:
            invalid_rows.append({
                "row_index": row_index,
                "reason": "Missing payee_name.",
                "raw_data": row,
            })
            continue

        # 4. Check for duplicates
        is_dup = False
        if rec_id in seen_record_ids:
            duplicate_count += 1
            is_dup = True
        if txn_id and txn_id in seen_txns:
            duplicate_count += 1
            is_dup = True
        if utr_rrn and utr_rrn in seen_utrs:
            duplicate_count += 1
            is_dup = True

        if is_dup:
            warnings.append(f"Row {row_index}: Duplicate reference detected ({txn_id or utr_rrn}). Kept first occurrence.")
            continue

        seen_record_ids.add(rec_id)
        if txn_id:
            seen_txns.add(txn_id)
        if utr_rrn:
            seen_utrs.add(utr_rrn)

        parsed_record = {
            "record_id": rec_id,
            "transaction_id": txn_id,
            "utr_rrn": utr_rrn,
            "transaction_date": (row.get(header_map.get("transaction_date", "")) or "").strip(),
            "transaction_time": (row.get(header_map.get("transaction_time", "")) or "").strip(),
            "amount_inr": amt_float,
            "currency": (row.get(header_map.get("currency", "")) or "INR").strip(),
            "payer_display_name": (row.get(header_map.get("payer_display_name", "")) or "").strip(),
            "payer_account_masked": (row.get(header_map.get("payer_account_masked", "")) or "").strip(),
            "payee_name": payee_name,
            "payee_vpa": payee_vpa,
            "bank_or_app_label": (row.get(header_map.get("bank_or_app_label", "")) or "").strip(),
            "transaction_status": (row.get(header_map.get("transaction_status", "")) or "SUCCESS").strip().upper(),
            "dataset_type": (row.get(header_map.get("dataset_type", "")) or "SYNTHETIC_DEMO").strip(),
            "verification_status": MANDATORY_DEMO_NOTICE,
            "notes": (row.get(header_map.get("notes", "")) or "").strip(),
        }
        valid_records.append(parsed_record)

    is_valid = len(valid_records) > 0 and len(invalid_rows) == 0

    return {
        "is_valid": is_valid,
        "filename": filename,
        "total_rows": row_index,
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_rows),
        "duplicate_count": duplicate_count,
        "warnings": warnings,
        "preview_records": valid_records[:8],
        "valid_records": valid_records,
        "invalid_rows": invalid_rows,
        "demo_data_notice": MANDATORY_DEMO_NOTICE,
    }


def activate_dataset(
    csv_bytes_or_text: Union[bytes, str],
    filename: str,
    admin_user: Dict[str, Any],
    dataset_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validates and activates a new reference dataset inside an atomic transaction.
    If the replacement fails, rolls back completely: previous active dataset is preserved.
    """
    validation = validate_csv_content(csv_bytes_or_text, filename)
    if not validation["is_valid"] or not validation["valid_records"]:
        err_msg = validation.get("error") or "CSV dataset validation failed."
        if validation["invalid_rows"]:
            reasons = [f"Row {r['row_index']}: {r['reason']}" for r in validation["invalid_rows"][:3]]
            err_msg += f" Reasons: {'; '.join(reasons)}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    valid_records = validation["valid_records"]
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        # Determine next dataset version
        latest_ds = session.query(ScreenshotDataset).order_by(ScreenshotDataset.version.desc()).first()
        next_version = (latest_ds.version + 1) if latest_ds else 1

        # 1. Deactivate existing active dataset
        active_previous = session.query(ScreenshotDataset).filter_by(is_active=True).all()
        for prev in active_previous:
            prev.is_active = False
            prev.deactivated_at = now_utc

        # 2. Insert new active dataset
        new_ds_id = f"DS-2026-{uuid.uuid4().hex[:12].upper()}"
        clean_name = (dataset_name or filename or f"Reference Dataset v{next_version}").strip()

        new_dataset = ScreenshotDataset(
            dataset_id=new_ds_id,
            filename=filename,
            dataset_name=clean_name,
            dataset_type="Demonstration Synthetic Dataset",
            version=next_version,
            is_active=True,
            total_records=len(valid_records),
            valid_records=len(valid_records),
            invalid_records=0,
            uploaded_by_erp_id=admin_erp_id,
            uploaded_by_name=admin_name,
            notes=f"Active reference dataset with {len(valid_records)} records. {MANDATORY_DEMO_NOTICE}.",
            created_at=now_utc,
            activated_at=now_utc,
        )
        session.add(new_dataset)
        session.flush()

        # 3. Bulk insert transaction records
        records_to_insert = []
        for rec in valid_records:
            records_to_insert.append(
                ScreenshotTransactionRecord(
                    dataset_id=new_dataset.id,
                    record_id=rec["record_id"],
                    transaction_id=rec["transaction_id"],
                    utr_rrn=rec["utr_rrn"],
                    transaction_date=rec["transaction_date"],
                    transaction_time=rec["transaction_time"],
                    amount_inr=rec["amount_inr"],
                    currency=rec["currency"],
                    payer_display_name=rec["payer_display_name"],
                    payer_account_masked=rec["payer_account_masked"],
                    payee_name=rec["payee_name"],
                    payee_vpa=rec["payee_vpa"],
                    bank_or_app_label=rec["bank_or_app_label"],
                    transaction_status=rec["transaction_status"],
                    dataset_type=rec["dataset_type"],
                    verification_status=MANDATORY_DEMO_NOTICE,
                    notes=rec["notes"],
                    created_at=now_utc,
                )
            )
        session.bulk_save_objects(records_to_insert)

        # 4. Security Audit Log
        audit_log = SecurityAuditLog(
            event_id=f"AUD-DS-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="SCREENSHOT_DATASET_ACTIVATED",
            target_resource_type="screenshot_dataset",
            target_resource_id=new_ds_id,
            outcome="SUCCESS",
            details=json.dumps({
                "filename": filename,
                "version": next_version,
                "records_imported": len(valid_records),
            }),
            created_at=now_utc,
        )
        session.add(audit_log)

        # Commit entire atomic transaction
        session.commit()

        return {
            "success": True,
            "dataset_id": new_ds_id,
            "version": next_version,
            "dataset_name": clean_name,
            "filename": filename,
            "total_records": len(valid_records),
            "activated_at": now_utc.isoformat(),
            "uploaded_by": admin_name,
            "verification_status": MANDATORY_DEMO_NOTICE,
            "message": f"Dataset v{next_version} ({clean_name}) successfully activated with {len(valid_records)} records.",
        }

    except Exception as exc:
        session.rollback()
        logger.error("Failed to activate screenshot dataset: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate dataset: {str(exc)}",
        )
    finally:
        session.close()


def get_active_dataset_info() -> Dict[str, Any]:
    """Retrieves current active reference dataset metadata."""
    session = SessionLocal()
    try:
        active = session.query(ScreenshotDataset).filter_by(is_active=True).first()
        if not active:
            return {
                "active": False,
                "message": "No screenshot reference dataset has been uploaded yet.",
                "demo_notice": MANDATORY_DEMO_NOTICE,
            }

        return {
            "active": True,
            "id": active.id,
            "dataset_id": active.dataset_id,
            "dataset_name": active.dataset_name,
            "filename": active.filename,
            "version": active.version,
            "total_records": active.total_records,
            "dataset_type": active.dataset_type,
            "uploaded_by": active.uploaded_by_name or active.uploaded_by_erp_id or "CyberAdmin",
            "activated_at": active.activated_at.isoformat() if active.activated_at else active.created_at.isoformat(),
            "demo_notice": MANDATORY_DEMO_NOTICE,
        }
    finally:
        session.close()


def deactivate_active_dataset(admin_user: Dict[str, Any]) -> Dict[str, Any]:
    """Deactivates active dataset without deleting historical data."""
    now_utc = datetime.now(timezone.utc)
    admin_erp_id = str(admin_user.get("id") or admin_user.get("erp_user_id") or admin_user.get("email") or "")
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"

    session = SessionLocal()
    try:
        active = session.query(ScreenshotDataset).filter_by(is_active=True).first()
        if not active:
            return {
                "success": False,
                "message": "No dataset is currently active.",
            }

        active.is_active = False
        active.deactivated_at = now_utc

        # Security Audit Log
        audit_log = SecurityAuditLog(
            event_id=f"AUD-DS-DEACT-{uuid.uuid4().hex[:16]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="SCREENSHOT_DATASET_DEACTIVATED",
            target_resource_type="screenshot_dataset",
            target_resource_id=active.dataset_id,
            outcome="SUCCESS",
            details=json.dumps({"version": active.version, "dataset_id": active.dataset_id}),
            created_at=now_utc,
        )
        session.add(audit_log)

        session.commit()
        return {
            "success": True,
            "message": f"Dataset v{active.version} ({active.dataset_name}) has been deactivated.",
        }
    except Exception as exc:
        session.rollback()
        logger.error("Failed to deactivate dataset: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate dataset.",
        )
    finally:
        session.close()


def get_dataset_history() -> List[Dict[str, Any]]:
    """Retrieves chronological dataset version history for CyberAdmin review."""
    session = SessionLocal()
    try:
        datasets = session.query(ScreenshotDataset).order_by(ScreenshotDataset.created_at.desc()).all()
        history = []
        for ds in datasets:
            history.append({
                "id": ds.id,
                "dataset_id": ds.dataset_id,
                "dataset_name": ds.dataset_name,
                "filename": ds.filename,
                "version": ds.version,
                "is_active": ds.is_active,
                "total_records": ds.total_records,
                "uploaded_by": ds.uploaded_by_name or ds.uploaded_by_erp_id or "CyberAdmin",
                "created_at": ds.created_at.isoformat() if ds.created_at else None,
                "activated_at": ds.activated_at.isoformat() if ds.activated_at else None,
                "deactivated_at": ds.deactivated_at.isoformat() if ds.deactivated_at else None,
            })
        return history
    finally:
        session.close()


# ==============================================================================
# DATASET MATCHING ENGINE
# ==============================================================================

def match_screenshot_against_active_dataset(
    extracted_fields: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compares OCR-extracted fields against the active transaction reference dataset.
    Replaces prefix-based heuristics with reference matching.

    Classifications:
    - MATCHING_DEMO_RECORD
    - DETAILS_MISMATCH
    - PARTIAL_MATCH
    - NO_MATCHING_RECORD
    - INSUFFICIENT_INFORMATION
    - NO_ACTIVE_DATASET
    """
    session = SessionLocal()
    try:
        active_ds = session.query(ScreenshotDataset).filter_by(is_active=True).first()
        if not active_ds:
            return {
                "classification": "NO_ACTIVE_DATASET",
                "heading": "No Active Reference Dataset",
                "message": (
                    "No reference dataset has been uploaded or activated by CyberAdmin. "
                    "The transaction cannot be verified against campus records."
                ),
                "demo_notice": MANDATORY_DEMO_NOTICE,
                "matched_record": None,
                "mismatches": [],
                "comparison_fields": [],
                "risk_score": 40,
                "status": "suspicious",
            }

        # 1. Normalize extracted fields
        raw_utr = (extracted_fields.get("bank_ref") or extracted_fields.get("utr_rrn") or "").strip()
        # Clean common OCR labels if embedded in string
        if raw_utr.upper().startswith(("UTR", "RRN", "REF")):
            raw_utr = re.sub(r"^(?:UTR|RRN|REF|NO)[:\s\-]*", "", raw_utr, flags=re.I).strip()
        # Normalized UTR: preserve digits only
        norm_utr = re.sub(r"[^0-9]", "", raw_utr)

        extracted_payee = (extracted_fields.get("payee_name") or extracted_fields.get("merchant_name") or "").strip()
        extracted_tid = (extracted_fields.get("transaction_id") or extracted_fields.get("txn_id") or "").strip()
        if extracted_tid.upper().startswith(("TRANSACTION", "TXN")):
            extracted_tid = re.sub(r"^(?:TRANSACTION|TXN|ID|NO)[:\s\-]*", "", extracted_tid, flags=re.I).strip()

        extracted_amt = None
        raw_amt = extracted_fields.get("amount")
        if raw_amt is not None:
            try:
                extracted_amt = float(str(raw_amt).replace(",", "").strip())
            except (ValueError, TypeError):
                extracted_amt = None

        extracted_vpa = (extracted_fields.get("payee_vpa") or extracted_fields.get("upi_id") or "").strip().lower()
        extracted_date = extracted_fields.get("transaction_date") or extracted_fields.get("date")
        extracted_time = extracted_fields.get("transaction_time") or extracted_fields.get("time")
        extracted_account = extracted_fields.get("payer_account_masked")

        # Step 1 & Result D: Check if UTR could be extracted reliably
        if not norm_utr or len(norm_utr) < 8:
            return {
                "classification": "UNABLE_TO_VERIFY_OCR_UNCERTAIN",
                "legacy_classification": "INSUFFICIENT_INFORMATION",
                "heading": "Unable to Verify — OCR Uncertain",
                "message": (
                    "The UTR/RRN could not be read reliably from the screenshot. "
                    "Please upload a clearer, uncropped image of the receipt."
                ),
                "demo_notice": MANDATORY_DEMO_NOTICE,
                "dataset_version": active_ds.version,
                "matched_record": None,
                "mismatches": [],
                "comparison_fields": [
                    {
                        "field": "UTR / RRN",
                        "screenshot_value": "Could not reliably extract",
                        "dataset_value": "—",
                        "matched": False,
                        "result": "OCR Uncertain",
                    },
                    {
                        "field": "Recipient / Paid Name",
                        "screenshot_value": extracted_payee or "—",
                        "dataset_value": "—",
                        "matched": False,
                        "result": "OCR Uncertain",
                    },
                ],
                "primary_comparison": [
                    {
                        "field": "UTR / RRN",
                        "screenshot_value": "Could not reliably extract",
                        "dataset_value": "—",
                        "matched": False,
                        "result": "OCR Uncertain",
                    },
                    {
                        "field": "Recipient / Paid Name",
                        "screenshot_value": extracted_payee or "—",
                        "dataset_value": "—",
                        "matched": False,
                        "result": "OCR Uncertain",
                    },
                ],
                "informational_fields": [
                    {"field": "Transaction ID", "screenshot_value": extracted_tid or "Could not reliably extract", "dataset_value": "—", "is_informational": True},
                    {"field": "Amount", "screenshot_value": f"₹{extracted_amt:,.2f}" if extracted_amt else "Could not reliably extract", "dataset_value": "—", "is_informational": True},
                    {"field": "Date & Time", "screenshot_value": f"{extracted_date or ''} {extracted_time or ''}".strip() or "—", "dataset_value": "—", "is_informational": True},
                    {"field": "Recipient UPI ID", "screenshot_value": extracted_vpa or "—", "dataset_value": "—", "is_informational": True},
                ],
                "risk_score": 40,
                "status": "suspicious",
            }

        # Step 2 & 3: Search active reference dataset for exact normalized UTR/RRN match
        all_ds_records = session.query(ScreenshotTransactionRecord).filter_by(dataset_id=active_ds.id).all()
        matching_records = [
            r for r in all_ds_records
            if re.sub(r"[^0-9]", "", str(r.utr_rrn or "").strip()) == norm_utr
        ]

        # Result E: Multiple or duplicate UTR records
        if len(matching_records) > 1:
            return {
                "classification": "AMBIGUOUS_DATASET_RECORD",
                "legacy_classification": "DETAILS_MISMATCH",
                "heading": "Ambiguous Dataset Record",
                "message": (
                    f"Multiple records ({len(matching_records)}) in the active reference dataset share the UTR/RRN '{norm_utr}'. "
                    "This record is ambiguous and requires administrative review by CyberAdmin."
                ),
                "demo_notice": MANDATORY_DEMO_NOTICE,
                "dataset_version": active_ds.version,
                "matched_record": None,
                "mismatches": ["Duplicate UTR reference found in active reference dataset."],
                "comparison_fields": [
                    {
                        "field": "UTR / RRN",
                        "screenshot_value": raw_utr,
                        "dataset_value": f"Multiple matches ({len(matching_records)})",
                        "matched": False,
                        "result": "Ambiguous",
                    },
                    {
                        "field": "Recipient / Paid Name",
                        "screenshot_value": extracted_payee or "—",
                        "dataset_value": "Multiple candidates",
                        "matched": False,
                        "result": "Ambiguous",
                    },
                ],
                "primary_comparison": [
                    {
                        "field": "UTR / RRN",
                        "screenshot_value": raw_utr,
                        "dataset_value": f"Multiple matches ({len(matching_records)})",
                        "matched": False,
                        "result": "Ambiguous",
                    },
                    {
                        "field": "Recipient / Paid Name",
                        "screenshot_value": extracted_payee or "—",
                        "dataset_value": "Multiple candidates",
                        "matched": False,
                        "result": "Ambiguous",
                    },
                ],
                "risk_score": 50,
                "status": "suspicious",
            }

        # Result C: UTR Not Found in active dataset
        if len(matching_records) == 0:
            return {
                "classification": "NO_MATCHING_RECORD",
                "legacy_classification": "NO_MATCHING_RECORD",
                "heading": "No Matching Reference Record",
                "message": (
                    "The UTR/RRN was not found in the currently active demonstration dataset. "
                    "This does not, by itself, prove that the payment is fake."
                ),
                "demo_notice": MANDATORY_DEMO_NOTICE,
                "dataset_version": active_ds.version,
                "matched_record": None,
                "mismatches": [],
                "comparison_fields": [
                    {
                        "field": "UTR / RRN",
                        "screenshot_value": raw_utr,
                        "dataset_value": "Not in active dataset",
                        "matched": False,
                        "result": "No Match",
                    },
                    {
                        "field": "Recipient / Paid Name",
                        "screenshot_value": extracted_payee or "—",
                        "dataset_value": "—",
                        "matched": False,
                        "result": "No Match",
                    },
                ],
                "primary_comparison": [
                    {
                        "field": "UTR / RRN",
                        "screenshot_value": raw_utr,
                        "dataset_value": "Not in active dataset",
                        "matched": False,
                        "result": "No Match",
                    },
                    {
                        "field": "Recipient / Paid Name",
                        "screenshot_value": extracted_payee or "—",
                        "dataset_value": "—",
                        "matched": False,
                        "result": "No Match",
                    },
                ],
                "informational_fields": [
                    {"field": "Transaction ID", "screenshot_value": extracted_tid or "—", "dataset_value": "—", "is_informational": True},
                    {"field": "Amount", "screenshot_value": f"₹{extracted_amt:,.2f}" if extracted_amt else "—", "dataset_value": "—", "is_informational": True},
                    {"field": "Date & Time", "screenshot_value": f"{extracted_date or ''} {extracted_time or ''}".strip() or "—", "dataset_value": "—", "is_informational": True},
                    {"field": "Recipient UPI ID", "screenshot_value": extracted_vpa or "—", "dataset_value": "—", "is_informational": True},
                ],
                "risk_score": 45,
                "status": "suspicious",
            }

        # Exactly 1 record found -> Compare Recipient Name
        candidate_record = matching_records[0]

        # Step 4: Compare recipient names with normalized token / containment logic
        norm_ext_payee = _normalize_string(extracted_payee)
        norm_ds_payee = _normalize_string(candidate_record.payee_name)

        ext_tokens = set(norm_ext_payee.split())
        ds_tokens = set(norm_ds_payee.split())
        common_tokens = ext_tokens & ds_tokens

        payee_match = (
            bool(norm_ext_payee and norm_ds_payee) and (
                norm_ext_payee == norm_ds_payee
                or norm_ext_payee in norm_ds_payee
                or norm_ds_payee in norm_ext_payee
                or len(common_tokens) >= 2
            )
        )

        matched_record_dict = {
            "record_id": candidate_record.record_id,
            "transaction_id": candidate_record.transaction_id,
            "utr_rrn": candidate_record.utr_rrn,
            "amount_inr": candidate_record.amount_inr,
            "payee_name": candidate_record.payee_name,
            "payee_vpa": candidate_record.payee_vpa,
            "transaction_date": candidate_record.transaction_date,
            "transaction_time": candidate_record.transaction_time,
            "payer_account_masked": candidate_record.payer_account_masked,
            "payer_display_name": candidate_record.payer_display_name,
            "bank_or_app_label": candidate_record.bank_or_app_label,
            "dataset_type": candidate_record.dataset_type,
            "verification_status": candidate_record.verification_status,
        }

        # Primary comparison rows (UTR & Recipient Name ONLY)
        primary_comparison = [
            {
                "field": "UTR / RRN",
                "screenshot_value": raw_utr,
                "dataset_value": candidate_record.utr_rrn,
                "matched": True,
                "result": "Match",
            },
            {
                "field": "Recipient / Paid Name",
                "screenshot_value": extracted_payee or "Could not reliably extract",
                "dataset_value": candidate_record.payee_name,
                "matched": payee_match,
                "result": "Match" if payee_match else "Mismatch",
            },
        ]

        # Informational fields (For reference display only; NOT part of primary decision)
        informational_fields = [
            {
                "field": "Transaction ID",
                "screenshot_value": extracted_tid or "Could not reliably extract",
                "dataset_value": candidate_record.transaction_id or "—",
                "matched": (extracted_tid.lower() == candidate_record.transaction_id.lower() if extracted_tid and candidate_record.transaction_id else True),
                "is_informational": True,
            },
            {
                "field": "Amount",
                "screenshot_value": f"₹{extracted_amt:,.2f}" if extracted_amt is not None else "Could not reliably extract",
                "dataset_value": f"₹{candidate_record.amount_inr:,.2f}" if candidate_record.amount_inr is not None else "—",
                "matched": (abs(extracted_amt - candidate_record.amount_inr) < 0.05 if extracted_amt is not None and candidate_record.amount_inr is not None else True),
                "is_informational": True,
            },
            {
                "field": "Transaction Date",
                "screenshot_value": extracted_date or "—",
                "dataset_value": candidate_record.transaction_date or "—",
                "matched": True,
                "is_informational": True,
            },
            {
                "field": "Transaction Time",
                "screenshot_value": extracted_time or "—",
                "dataset_value": candidate_record.transaction_time or "—",
                "matched": True,
                "is_informational": True,
            },
            {
                "field": "Recipient UPI ID",
                "screenshot_value": extracted_vpa or "—",
                "dataset_value": candidate_record.payee_vpa or "—",
                "matched": (extracted_vpa.lower() == candidate_record.payee_vpa.lower() if extracted_vpa and candidate_record.payee_vpa else True),
                "is_informational": True,
            },
            {
                "field": "Payer Account",
                "screenshot_value": extracted_account or "—",
                "dataset_value": candidate_record.payer_account_masked or "—",
                "matched": True,
                "is_informational": True,
            },
        ]

        # Result A: MATCH FOUND
        if payee_match:
            return {
                "classification": "REFERENCE_DATASET_MATCH",
                "legacy_classification": "MATCHING_DEMO_RECORD",
                "heading": "Reference Dataset Match",
                "match_method": "Exact UTR/RRN & Recipient Name Match",
                "message": (
                    "The extracted UTR/RRN and recipient name match a record in the active demonstration dataset. "
                    "This confirms presence in the demonstration dataset; it does not constitute bank payment verification."
                ),
                "demo_notice": MANDATORY_DEMO_NOTICE,
                "dataset_version": active_ds.version,
                "dataset_source": active_ds.dataset_name or active_ds.filename,
                "matched_record": matched_record_dict,
                "mismatches": [],
                "primary_comparison": primary_comparison,
                "informational_fields": informational_fields,
                "comparison_fields": primary_comparison + informational_fields,
                "risk_score": 15,
                "status": "safe",
            }

        # Result B: UTR MATCH BUT RECIPIENT NAME MISMATCH
        return {
            "classification": "RECIPIENT_NAME_MISMATCH",
            "legacy_classification": "DETAILS_MISMATCH",
            "heading": "Recipient Name Mismatch — Manual Verification Recommended",
            "match_method": "UTR Match with Recipient Discrepancy",
            "message": (
                f"The extracted UTR/RRN matches a dataset record, but the recipient name ('{extracted_payee}') "
                f"differs from the expected recipient ('{candidate_record.payee_name}'). "
                "Manual verification is recommended."
            ),
            "demo_notice": MANDATORY_DEMO_NOTICE,
            "dataset_version": active_ds.version,
            "dataset_source": active_ds.dataset_name or active_ds.filename,
            "matched_record": matched_record_dict,
            "mismatches": [
                f"Recipient Name Mismatch: Screenshot displays '{extracted_payee}', dataset record expects '{candidate_record.payee_name}'."
            ],
            "primary_comparison": primary_comparison,
            "informational_fields": informational_fields,
            "comparison_fields": primary_comparison + informational_fields,
            "risk_score": 65,
            "status": "suspicious",
        }

    finally:
        session.close()


# Backward compatibility aliases
validate_and_parse_csv = validate_csv_content

def activate_new_dataset(
    csv_bytes_or_text: Union[bytes, str] = None,
    filename: str = "dataset.csv",
    admin_user: Dict[str, Any] = None,
    dataset_name: Optional[str] = None,
    csv_content: Union[bytes, str] = None,
) -> Dict[str, Any]:
    content = csv_bytes_or_text if csv_bytes_or_text is not None else csv_content
    return activate_dataset(content, filename, admin_user, dataset_name)



