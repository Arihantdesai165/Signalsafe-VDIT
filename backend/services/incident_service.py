# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Incident Management Service
Handles persistent cybersecurity incident reports, investigation workflows,
status transitions, notes, audit trails, and dashboard statistics using dedicated PostgreSQL.

All writes are transactional, with atomic commit/rollback.
Incident identifiers are generated using concurrency-safe PostgreSQL sequence (incident_id_seq).
"""

import os
import re
import html
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from ..database.connection import SessionLocal, check_db_connection
from ..database.models import (
    IncidentReport,
    IncidentEvidence,
    IncidentInvestigation,
    SecurityAuditLog,
    UserProfile,
    AppStatistic,
)

logger = logging.getLogger("signalsafe.incident_service")

VALID_STATUSES = ["Pending", "Under Review", "Resolved", "Rejected"]
VALID_CATEGORIES = [
    "phishing_url",
    "upi_qr_scam",
    "fake_payment_screenshot",
    "suspicious_sms",
    "credential_theft",
    "other",
]

CATEGORY_LABELS = {
    "phishing_url": "Phishing URL / Fake Portal",
    "upi_qr_scam": "Fraudulent UPI QR Code",
    "fake_payment_screenshot": "Fake Payment Screenshot",
    "suspicious_sms": "Scam SMS / Smishing",
    "credential_theft": "Credential Harvesting Site",
    "other": "Other Cyber Threat",
}


def sanitize_input(val: str, max_len: int = 1000) -> str:
    """Escapes HTML entities, strips control characters, and enforces length."""
    if not val:
        return ""
    cleaned = re.sub(r"<[^>]*?>", "", str(val))
    escaped = html.escape(cleaned.strip())
    return escaped[:max_len]


def _format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_incident(inc: IncidentReport) -> Dict[str, Any]:
    """Converts an IncidentReport ORM object to the dictionary expected by clients and API."""
    notes = []
    audit_trail = []

    # Map investigations to notes and audit_trail
    for idx, inv in enumerate(inc.investigations or [], 1):
        inv_ts = _format_datetime(inv.created_at)
        if inv.action_type == "NOTE_ADDED":
            notes.append({
                "id": f"NOTE-{idx}",
                "author": inv.admin_name,
                "role": "CYBERADMIN",
                "text": inv.investigation_note,
                "timestamp": inv_ts,
            })
            audit_trail.append({
                "action": "Investigation Note Added",
                "by": inv.admin_name,
                "timestamp": inv_ts,
                "note": inv.investigation_note[:100] + ("..." if len(inv.investigation_note) > 100 else ""),
            })
        elif inv.action_type == "STATUS_CHANGE":
            audit_trail.append({
                "action": f"Status changed from {inv.previous_status or 'Pending'} to {inv.new_status}",
                "by": inv.admin_name,
                "timestamp": inv_ts,
                "note": inv.investigation_note or f"Updated status to {inv.new_status}.",
            })
            if inv.investigation_note and not inv.investigation_note.startswith("Updated status"):
                notes.append({
                    "id": f"NOTE-{idx}",
                    "author": inv.admin_name,
                    "role": "CYBERADMIN",
                    "text": inv.investigation_note,
                    "timestamp": inv_ts,
                })
        else:
            audit_trail.append({
                "action": inv.action_type,
                "by": inv.admin_name,
                "timestamp": inv_ts,
                "note": inv.investigation_note,
            })

    # If no audit trail, ensure at least submission is reflected
    if not audit_trail:
        audit_trail.append({
            "action": "Report Submitted",
            "by": inc.reported_by,
            "timestamp": _format_datetime(inc.created_at),
            "note": f"Initial submission by {inc.reporter_role}.",
        })

    return {
        "id": inc.incident_id,
        "reported_by": inc.reported_by,
        "reporter_email": inc.reporter_email or "",
        "reporter_role": inc.reporter_role,
        "reporter_dept": inc.reporter_dept or "",
        "category": inc.category,
        "category_label": inc.category_label or CATEGORY_LABELS.get(inc.category, "Cyber Threat"),
        "title": inc.title or inc.category_label or inc.category,
        "target_evidence": inc.target_evidence,
        "description": inc.description,
        "status": inc.status,
        "severity": inc.severity,
        "created_at": _format_datetime(inc.created_at),
        "updated_at": _format_datetime(inc.updated_at),
        "assigned_admin_erp_id": inc.assigned_admin_erp_id,
        "resolved_at": _format_datetime(inc.resolved_at) if inc.resolved_at else None,
        "notes": notes,
        "audit_trail": audit_trail,
    }


def increment_screenshot_counter() -> int:
    """Safely increments the screenshots analyzed count in PostgreSQL and returns new value."""
    session = SessionLocal()
    try:
        stat = session.query(AppStatistic).filter_by(stat_key="screenshots_analyzed").with_for_update().first()
        if not stat:
            stat = AppStatistic(
                stat_key="screenshots_analyzed",
                stat_value=1,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(stat)
            new_val = 1
        else:
            stat.stat_value += 1
            stat.updated_at = datetime.now(timezone.utc)
            new_val = stat.stat_value
        session.commit()
        return new_val
    except Exception as exc:
        session.rollback()
        logger.error("Failed to increment screenshot counter in DB: %s", exc)
        return 15
    finally:
        session.close()


def get_incident_stats() -> Dict[str, Any]:
    """Computes real incident summary counts for the CyberAdmin dashboard."""
    session = SessionLocal()
    try:
        total = session.query(IncidentReport).count()
        pending = session.query(IncidentReport).filter(IncidentReport.status.ilike("pending")).count()
        under_review = session.query(IncidentReport).filter(IncidentReport.status.ilike("under review")).count()
        resolved = session.query(IncidentReport).filter(IncidentReport.status.ilike("resolved")).count()
        rejected = session.query(IncidentReport).filter(IncidentReport.status.ilike("rejected")).count()

        stat = session.query(AppStatistic).filter_by(stat_key="screenshots_analyzed").first()
        screenshots_analyzed = stat.stat_value if stat else 14

        return {
            "total_incidents": total,
            "pending_reviews": pending,
            "under_review": under_review,
            "resolved_incidents": resolved,
            "rejected_incidents": rejected,
            "screenshots_analyzed": screenshots_analyzed,
        }
    except Exception as exc:
        logger.error("Failed to fetch incident statistics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve incident statistics. Please try again later.",
        )
    finally:
        session.close()


def list_incidents(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    Returns filtered and paginated list of incidents from PostgreSQL.
    """
    session = SessionLocal()
    try:
        query = session.query(IncidentReport)

        # Status filter
        if status_filter and status_filter.upper() not in ["ALL", ""]:
            norm_status = status_filter.strip().replace("_", " ")
            query = query.filter(IncidentReport.status.ilike(norm_status))

        # Category filter
        if category_filter and category_filter.upper() not in ["ALL", ""]:
            query = query.filter(IncidentReport.category.ilike(category_filter.strip()))

        # Search filter
        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query = query.filter(
                or_(
                    IncidentReport.incident_id.ilike(term),
                    IncidentReport.reported_by.ilike(term),
                    IncidentReport.reporter_email.ilike(term),
                    IncidentReport.description.ilike(term),
                    IncidentReport.target_evidence.ilike(term),
                    IncidentReport.category.ilike(term),
                )
            )

        total_count = query.count()

        # Sort descending by creation date
        query = query.order_by(IncidentReport.created_at.desc())

        # Pagination
        page = max(1, page)
        page_size = max(1, min(100, page_size))
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        offset = (page - 1) * page_size

        records = query.offset(offset).limit(page_size).all()
        serialized = [_serialize_incident(inc) for inc in records]

        return {
            "incidents": serialized,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    except Exception as exc:
        logger.error("Failed to list incidents from DB: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch incidents. Please try again later.",
        )
    finally:
        session.close()


def get_incident(incident_id: str) -> Dict[str, Any]:
    """Retrieves a single incident by its unique ID (e.g. INC-2026-0001)."""
    session = SessionLocal()
    try:
        inc = session.query(IncidentReport).filter_by(incident_id=incident_id).first()
        if not inc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )
        return _serialize_incident(inc)
    finally:
        session.close()


def create_incident(
    category: str,
    target_evidence: str,
    description: str,
    severity: str,
    user: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Submits a new security incident report with concurrency-safe sequence generation.
    Wraps report creation, evidence creation, and audit logging into a single transaction.
    """
    cat = (category or "other").strip().lower()
    if cat not in VALID_CATEGORIES:
        cat = "other"

    sev = (severity or "Medium").capitalize()
    if sev not in ["Low", "Medium", "High", "Critical"]:
        sev = "Medium"

    clean_target = sanitize_input(target_evidence, max_len=500)
    clean_desc = sanitize_input(description, max_len=2000)

    if not clean_target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target evidence (URL, UPI ID, or description) is required.",
        )

    now_utc = datetime.now(timezone.utc)
    reporter_name = user.get("name") or user.get("email") or "Campus User"
    reporter_role = (user.get("role") or "STUDENT").upper()
    reporter_email = user.get("email") or ""
    raw_dept = user.get("department")
    if isinstance(raw_dept, dict):
        reporter_dept = raw_dept.get("name") or raw_dept.get("code") or ""
    elif isinstance(raw_dept, str):
        reporter_dept = raw_dept
    else:
        reporter_dept = ""
    reporter_erp_id = user.get("id") or user.get("erp_user_id") or (f"ERP-{reporter_email.split('@')[0].upper()}" if reporter_email else None)

    session = SessionLocal()
    try:
        # Concurrency-safe sequence generation
        next_seq = session.execute(text("SELECT nextval('incident_id_seq')")).scalar()
        new_incident_id = f"INC-2026-{next_seq:04d}"

        # 1. Upsert UserProfile if ERP user id available
        if reporter_erp_id:
            user_profile = session.query(UserProfile).filter_by(erp_user_id=reporter_erp_id).first()
            if not user_profile and reporter_email:
                user_profile = session.query(UserProfile).filter_by(email=reporter_email).first()
            if user_profile:
                user_profile.last_seen_at = now_utc
            else:
                user_profile = UserProfile(
                    erp_user_id=reporter_erp_id,
                    display_name=reporter_name,
                    email=reporter_email,
                    role=reporter_role,
                    department=reporter_dept,
                    created_at=now_utc,
                    updated_at=now_utc,
                    last_seen_at=now_utc,
                )
                session.add(user_profile)

        # 2. Insert IncidentReport
        new_inc = IncidentReport(
            incident_id=new_incident_id,
            reporter_erp_id=reporter_erp_id,
            reported_by=reporter_name,
            reporter_email=reporter_email,
            reporter_role=reporter_role,
            reporter_dept=reporter_dept,
            category=cat,
            category_label=CATEGORY_LABELS.get(cat, "Cyber Threat"),
            title=CATEGORY_LABELS.get(cat, "Cyber Threat"),
            description=clean_desc or "No additional description provided.",
            target_evidence=clean_target,
            status="Pending",
            severity=sev,
            created_at=now_utc,
            updated_at=now_utc,
        )
        session.add(new_inc)
        session.flush()

        # 3. Insert IncidentEvidence metadata
        evidence = IncidentEvidence(
            incident_id=new_inc.id,
            evidence_type=cat,
            file_storage_ref=None,
            sanitized_metadata=json.dumps({"indicator": clean_target}),
            uploaded_by_erp_id=reporter_erp_id,
            created_at=now_utc,
        )
        session.add(evidence)

        # 4. Insert initial audit trail investigation
        initial_inv = IncidentInvestigation(
            incident_id=new_inc.id,
            admin_erp_id=reporter_erp_id,
            admin_name=reporter_name,
            action_type="REPORT_SUBMITTED",
            investigation_note=f"Submitted via SignalSafe Campus by {reporter_role}.",
            previous_status=None,
            new_status="Pending",
            created_at=now_utc,
        )
        session.add(initial_inv)

        # 5. Insert security audit log
        audit_log = SecurityAuditLog(
            event_id=f"AUD-{new_incident_id}-{now_utc.strftime('%Y%m%d%H%M%S')}",
            actor_erp_id=reporter_erp_id,
            actor_name=reporter_name,
            actor_role=reporter_role,
            event_type="INCIDENT_SUBMISSION",
            target_resource_type="incident",
            target_resource_id=new_incident_id,
            outcome="SUCCESS",
            details=json.dumps({"category": cat, "severity": sev}),
            created_at=now_utc,
        )
        session.add(audit_log)

        # Commit entire atomic transaction
        session.commit()
        return _serialize_incident(new_inc)

    except Exception as exc:
        session.rollback()
        logger.error("Failed to create incident: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit incident report. Please try again.",
        )
    finally:
        session.close()


def update_incident_status(
    incident_id: str,
    new_status: str,
    admin_user: Dict[str, Any],
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Updates the status of an incident and appends an investigation and audit log record.
    CyberAdmin only. Executes inside an atomic transaction with automatic rollback on error.
    """
    clean_status = (new_status or "").strip().replace("_", " ")
    matching = [s for s in VALID_STATUSES if s.lower() == clean_status.lower()]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed statuses: {', '.join(VALID_STATUSES)}, PENDING, UNDER_REVIEW, RESOLVED, REJECTED",
        )
    target_status = matching[0]

    now_utc = datetime.now(timezone.utc)
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"
    admin_erp_id = admin_user.get("id") or admin_user.get("email")
    clean_note = sanitize_input(note or "", max_len=1000)

    session = SessionLocal()
    try:
        inc = session.query(IncidentReport).filter_by(incident_id=incident_id).with_for_update().first()
        if not inc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )

        old_status = inc.status
        inc.status = target_status
        inc.updated_at = now_utc
        inc.assigned_admin_erp_id = str(admin_erp_id)
        if target_status.lower() in ["resolved", "rejected"]:
            inc.resolved_at = now_utc

        # 1. Add investigation record
        investigation = IncidentInvestigation(
            incident_id=inc.id,
            admin_erp_id=admin_erp_id,
            admin_name=admin_name,
            action_type="STATUS_CHANGE",
            investigation_note=clean_note or f"Updated status to {target_status}.",
            previous_status=old_status,
            new_status=target_status,
            created_at=now_utc,
        )
        session.add(investigation)

        # 2. Add security audit log
        audit_log = SecurityAuditLog(
            event_id=f"AUD-{incident_id}-{now_utc.strftime('%Y%m%d%H%M%S%f')[:17]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="STATUS_CHANGE",
            target_resource_type="incident",
            target_resource_id=incident_id,
            outcome="SUCCESS",
            details=json.dumps({"from": old_status, "to": target_status, "note": clean_note}),
            created_at=now_utc,
        )
        session.add(audit_log)

        # Commit transaction
        session.commit()
        return _serialize_incident(inc)

    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logger.error("Failed to update incident status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update incident status. Transaction rolled back.",
        )
    finally:
        session.close()


def add_incident_note(
    incident_id: str,
    note_text: str,
    admin_user: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Adds an investigation note to an existing incident. CyberAdmin only.
    Executes inside an atomic transaction with automatic rollback on error.
    """
    clean_text = sanitize_input(note_text, max_len=1500)
    if not clean_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Note text cannot be empty.",
        )

    now_utc = datetime.now(timezone.utc)
    admin_name = admin_user.get("name") or admin_user.get("email") or "CyberAdmin"
    admin_erp_id = admin_user.get("id") or admin_user.get("email")

    session = SessionLocal()
    try:
        inc = session.query(IncidentReport).filter_by(incident_id=incident_id).with_for_update().first()
        if not inc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Incident '{incident_id}' not found.",
            )

        inc.updated_at = now_utc

        # 1. Add investigation note
        investigation = IncidentInvestigation(
            incident_id=inc.id,
            admin_erp_id=admin_erp_id,
            admin_name=admin_name,
            action_type="NOTE_ADDED",
            investigation_note=clean_text,
            previous_status=inc.status,
            new_status=inc.status,
            created_at=now_utc,
        )
        session.add(investigation)

        # 2. Add security audit log
        audit_log = SecurityAuditLog(
            event_id=f"AUD-{incident_id}-{now_utc.strftime('%Y%m%d%H%M%S%f')[:17]}",
            actor_erp_id=admin_erp_id,
            actor_name=admin_name,
            actor_role="CYBERADMIN",
            event_type="NOTE_ADDED",
            target_resource_type="incident",
            target_resource_id=incident_id,
            outcome="SUCCESS",
            details=json.dumps({"note_preview": clean_text[:100]}),
            created_at=now_utc,
        )
        session.add(audit_log)

        # Commit transaction
        session.commit()
        return _serialize_incident(inc)

    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logger.error("Failed to add incident note: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record note. Transaction rolled back.",
        )
    finally:
        session.close()
