# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Incidents Router
Provides API endpoints for incident report submission, review,
status tracking, investigation notes, and CyberAdmin dashboard analytics.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query, HTTPException, status

from ..services.auth_service import get_current_user, require_cyberadmin
from ..services.incident_service import (
    get_incident_stats,
    list_incidents,
    get_incident,
    create_incident,
    update_incident_status,
    add_incident_note,
)
from ..services.url_service import analyze_url

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


class IncidentCreateRequest(BaseModel):
    category: str = Field(..., description="phishing_url, upi_qr_scam, fake_payment_screenshot, suspicious_sms, credential_theft, other")
    target_evidence: str = Field(..., description="Suspicious URL, phone number, UPI ID, or transaction ID")
    description: str = Field(..., description="Details regarding the incident")
    severity: Optional[str] = Field("Medium", description="Low, Medium, High, or Critical")


class IncidentStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Pending, Under Review, Resolved, or Rejected")
    note: Optional[str] = Field(None, description="Optional investigation note explaining status transition")


class IncidentNoteRequest(BaseModel):
    note: str = Field(..., description="Investigation note content")


@router.get("/stats")
async def get_incident_statistics_endpoint(
    current_admin: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Returns authentic incident overview metrics and statistics.
    Accessible exclusively to authenticated CyberAdmin.
    """
    return get_incident_stats()


@router.get("")
async def list_incidents_endpoint(
    search: Optional[str] = Query(None, description="Search term for ID, reporter, or description"),
    status: Optional[str] = Query(None, description="Filter by status: Pending, Under Review, Resolved, Rejected"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_admin: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Lists cybersecurity incidents with filtering and pagination.
    Accessible exclusively to authenticated CyberAdmin.
    """
    return list_incidents(
        search=search,
        status_filter=status,
        category_filter=category,
        page=page,
        page_size=page_size,
    )


@router.get("/{incident_id}")
async def get_incident_detail_endpoint(
    incident_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Retrieves full details for a single incident report.
    CyberAdmin can access any report; students/faculty can only access their own submissions.
    """
    incident = get_incident(incident_id)

    user_role = (current_user.get("role") or "").upper().strip()
    user_email = (current_user.get("email") or "").lower().strip()
    reporter_email = (incident.get("reporter_email") or "").lower().strip()

    if user_role != "CYBERADMIN" and user_email != reporter_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view security incidents reported by your account.",
        )

    return incident


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_incident_endpoint(
    payload: IncidentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Submits a new cybersecurity incident report.
    Available to all authenticated campus users (Students, Faculty, Staff, and CyberAdmin).
    """
    new_report = create_incident(
        category=payload.category,
        target_evidence=payload.target_evidence,
        description=payload.description,
        severity=payload.severity or "Medium",
        user=current_user,
    )
    return new_report


@router.patch("/{incident_id}/status")
async def update_status_endpoint(
    incident_id: str,
    payload: IncidentStatusUpdateRequest,
    current_admin: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Updates status and writes an audit log entry for the incident.
    CyberAdmin exclusive.
    """
    updated = update_incident_status(
        incident_id=incident_id,
        new_status=payload.status,
        admin_user=current_admin,
        note=payload.note,
    )
    return updated


@router.post("/{incident_id}/notes")
async def add_note_endpoint(
    incident_id: str,
    payload: IncidentNoteRequest,
    current_admin: Dict[str, Any] = Depends(require_cyberadmin),
):
    """
    Appends an investigation note to the incident record.
    CyberAdmin exclusive.
    """
    updated = add_incident_note(
        incident_id=incident_id,
        note_text=payload.note,
        admin_user=current_admin,
    )
    return updated
