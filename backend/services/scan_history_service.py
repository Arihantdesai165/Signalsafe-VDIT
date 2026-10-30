# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Scan History & Threat Intelligence Service
Manages persistent storage of scan results (Screenshots, URLs, QR Codes),
community threat reports, and security audit event logging in PostgreSQL.
"""

import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..database.connection import SessionLocal
from ..database.models import (
    ScreenshotScanResult,
    URLScanResult,
    QRScanResult,
    CommunityReportedURL,
    SecurityAuditLog,
)

logger = logging.getLogger("signalsafe.scan_history")


def save_screenshot_scan(
    result: Dict[str, Any],
    user: Dict[str, Any],
    engine_version: str = "SignalSafe-OCR-v2.0",
) -> Optional[str]:
    """
    Persists the actual result produced by the screenshot detector.
    Does not alter or invent model predictions or risk scores.
    """
    session = SessionLocal()
    scan_id = f"SCAN-SS-{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)

    user_erp_id = user.get("id") or user.get("erp_user_id") or user.get("email") or "ANONYMOUS"
    detection_result = str(result.get("status") or "unknown")
    risk_score = float(result.get("risk_score", 0.0))

    metadata = {
        "reasons": result.get("reasons", []),
        "extracted_fields": result.get("extracted_fields", {}),
        "confidence": result.get("confidence", "medium"),
        "evidence_summary": result.get("evidence_summary", ""),
        "classification": result.get("classification"),
        "demo_notice": result.get("demo_notice"),
        "comparison_fields": result.get("comparison_fields", []),
        "mismatches": result.get("mismatches", []),
        "matched_record": result.get("matched_record"),
        "app_identified": result.get("app_identified"),
        "ml_prediction": result.get("ml_prediction"),
        "ml_confidence": result.get("ml_confidence"),
        "layout_valid": result.get("layout_valid"),
    }

    try:
        scan_record = ScreenshotScanResult(
            scan_id=scan_id,
            user_erp_id=user_erp_id,
            detection_result=detection_result,
            risk_score=risk_score,
            detection_metadata=json.dumps(metadata),
            engine_version=engine_version,
            created_at=now_utc,
        )
        session.add(scan_record)
        session.commit()
        return scan_id
    except Exception as exc:
        session.rollback()
        logger.error("Failed to persist screenshot scan result: %s", exc)
        return None
    finally:
        session.close()


def save_url_scan(
    result: Dict[str, Any],
    normalized_url: str,
    user: Dict[str, Any],
    report_count: int = 0,
) -> Optional[str]:
    """
    Persists scan results from website safety and malicious link scanner.
    Maintains existing URL validation and SSRF protections without visiting arbitrary URLs.
    """
    session = SessionLocal()
    scan_id = f"SCAN-URL-{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)

    user_erp_id = user.get("id") or user.get("erp_user_id") or user.get("email") or "ANONYMOUS"
    detection_result = str(result.get("status") or "unknown")
    risk_score = float(result.get("risk_score", 0.0))

    metadata = {
        "reasons": result.get("reasons", []),
        "extracted_fields": result.get("extracted_fields", {}),
        "confidence": result.get("confidence", "medium"),
        "evidence_summary": result.get("evidence_summary", ""),
    }

    try:
        scan_record = URLScanResult(
            scan_id=scan_id,
            user_erp_id=user_erp_id,
            normalized_url=normalized_url,
            detection_result=detection_result,
            risk_score=risk_score,
            detection_metadata=json.dumps(metadata),
            report_count=report_count,
            created_at=now_utc,
        )
        session.add(scan_record)
        session.commit()
        return scan_id
    except Exception as exc:
        session.rollback()
        logger.error("Failed to persist URL scan result: %s", exc)
        return None
    finally:
        session.close()


def save_qr_scan(
    result: Dict[str, Any],
    user: Dict[str, Any],
) -> Optional[str]:
    """
    Persists the actual QR scanning results and extracted information.
    """
    session = SessionLocal()
    scan_id = f"SCAN-QR-{uuid.uuid4().hex[:16]}"
    now_utc = datetime.now(timezone.utc)

    user_erp_id = user.get("id") or user.get("erp_user_id") or user.get("email") or "ANONYMOUS"
    detection_result = str(result.get("status") or "unknown")
    risk_score = float(result.get("risk_score", 0.0))

    extracted = result.get("extracted_fields") or {}
    dest = (
        result.get("decoded_data")
        or (extracted.get("payee_address") if isinstance(extracted, dict) else None)
        or "None"
    )

    metadata = {
        "reasons": result.get("reasons", []),
        "extracted_fields": extracted,
        "confidence": result.get("confidence", "medium"),
        "decoded_data": result.get("decoded_data", ""),
        "evidence_summary": result.get("evidence_summary", ""),
        "classification": result.get("classification"),
        "heading": result.get("heading"),
        "is_college_verified": result.get("is_college_verified", False),
        "registered_display_name": result.get("registered_display_name"),
        "payment_purpose": result.get("payment_purpose"),
        "department": result.get("department"),
        "matched_fields": result.get("matched_fields", []),
        "differing_fields": result.get("differing_fields", []),
        "registry_notice": result.get("registry_notice"),
    }

    try:
        scan_record = QRScanResult(
            scan_id=scan_id,
            user_erp_id=user_erp_id,
            extracted_destination=dest,
            detection_result=detection_result,
            risk_score=risk_score,
            detection_metadata=json.dumps(metadata),
            created_at=now_utc,
        )
        session.add(scan_record)
        session.commit()
        return scan_id
    except Exception as exc:
        session.rollback()
        logger.error("Failed to persist QR scan result: %s", exc)
        return None
    finally:
        session.close()


def get_url_report_count(url: str) -> int:
    """
    Loads community report count for a normalized URL from PostgreSQL.
    Replaces legacy JSON reads with safe DB lookup.
    """
    if not url:
        return 0
    clean_url = url.strip().lower()

    session = SessionLocal()
    try:
        record = session.query(CommunityReportedURL).filter_by(url_key=clean_url).first()
        return record.report_count if record else 0
    except Exception as exc:
        logger.warning("Could not query community report count from DB: %s", exc)
        return 0
    finally:
        session.close()


def record_url_report(url: str, user: Dict[str, Any]) -> int:
    """
    Increments report count for a URL in PostgreSQL and creates an audit log entry.
    Replaces runtime write to reports.json.
    """
    clean_url = url.strip().lower()
    now_utc = datetime.now(timezone.utc)
    user_erp_id = user.get("id") or user.get("erp_user_id") or user.get("email") or "ANONYMOUS"
    user_name = user.get("name") or user.get("email") or "Campus User"
    user_role = (user.get("role") or "STUDENT").upper()

    session = SessionLocal()
    try:
        record = session.query(CommunityReportedURL).filter_by(url_key=clean_url).with_for_update().first()
        if record:
            record.report_count += 1
            record.last_reported_at = now_utc
            new_count = record.report_count
        else:
            new_record = CommunityReportedURL(
                url_key=clean_url,
                report_count=1,
                last_reported_at=now_utc,
            )
            session.add(new_record)
            new_count = 1

        # Audit log entry for community threat report
        audit_log = SecurityAuditLog(
            event_id=f"AUD-REP-{uuid.uuid4().hex[:16]}",
            actor_erp_id=user_erp_id,
            actor_name=user_name,
            actor_role=user_role,
            event_type="COMMUNITY_URL_REPORTED",
            target_resource_type="url",
            target_resource_id=clean_url[:100],
            outcome="SUCCESS",
            details=json.dumps({"url": clean_url[:255], "report_count": new_count}),
            created_at=now_utc,
        )
        session.add(audit_log)

        session.commit()
        return new_count
    except Exception as exc:
        session.rollback()
        logger.error("Failed to record URL report in DB: %s", exc)
        return 1
    finally:
        session.close()


def record_audit_event(
    event_type: str,
    actor_erp_id: Optional[str] = None,
    actor_name: Optional[str] = None,
    actor_role: Optional[str] = None,
    target_resource_type: str = "system",
    target_resource_id: Optional[str] = None,
    outcome: str = "SUCCESS",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> Optional[str]:
    """
    Records an immutable security audit event.
    Never logs passwords, tokens, cookies, or unnecessary sensitive data.
    """
    session = SessionLocal()
    event_id = f"AUD-{uuid.uuid4().hex[:20]}"
    now_utc = datetime.now(timezone.utc)

    # Sanitize details: strictly remove sensitive keys
    sanitized_details = {}
    if details and isinstance(details, dict):
        for k, v in details.items():
            if any(secret_term in k.lower() for secret_term in ["password", "token", "secret", "cookie", "otp"]):
                continue
            sanitized_details[k] = str(v)[:500]

    try:
        log_entry = SecurityAuditLog(
            event_id=event_id,
            actor_erp_id=actor_erp_id,
            actor_name=actor_name,
            actor_role=actor_role,
            event_type=event_type,
            target_resource_type=target_resource_type,
            target_resource_id=target_resource_id,
            outcome=outcome,
            details=json.dumps(sanitized_details) if sanitized_details else None,
            ip_address=ip_address,
            created_at=now_utc,
        )
        session.add(log_entry)
        session.commit()
        return event_id
    except Exception as exc:
        session.rollback()
        logger.error("Failed to record security audit log: %s", exc)
        return None
    finally:
        session.close()
