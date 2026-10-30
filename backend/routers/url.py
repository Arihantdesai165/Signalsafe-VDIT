# -*- coding: utf-8 -*-
"""API router for URL and phishing detection."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..services.url_service import analyze_url
from ..services.auth_service import get_current_user
from ..services.scan_history_service import (
    get_url_report_count,
    record_url_report,
    save_url_scan,
)


class URLRequest(BaseModel):
    url: str


router = APIRouter(prefix="/api/url", tags=["URL"])


@router.post("/analyze")
async def analyze_url_endpoint(
    request: URLRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Analyze URL via standard endpoint. Requires SignalSafe authentication.
    Queries community threat intelligence and persists scan result to PostgreSQL.
    """
    result = analyze_url(request.url)
    result["url"] = request.url

    # Query persistent community report count from dedicated PostgreSQL
    report_count = get_url_report_count(request.url)
    result["report_count"] = report_count

    # Persist scan result to PostgreSQL
    scan_id = save_url_scan(result, request.url, current_user, report_count)
    if scan_id:
        result["scan_id"] = scan_id

    return result


@router.post("/phishing/analyze")
async def analyze_phishing_endpoint(
    request: URLRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Dedicated phishing analysis endpoint.
    Returns hybrid risk score (ML + Rules).
    Requires SignalSafe authentication.
    """
    result = analyze_url(request.url)
    result["url"] = request.url

    # Query persistent community report count from dedicated PostgreSQL
    report_count = get_url_report_count(request.url)
    result["report_count"] = report_count

    # Persist scan result to PostgreSQL
    scan_id = save_url_scan(result, request.url, current_user, report_count)
    if scan_id:
        result["scan_id"] = scan_id

    return result


@router.post("/report")
async def report_url_endpoint(
    request: URLRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Report a URL as a community threat.
    Persists count and audit log in dedicated PostgreSQL.
    """
    new_count = record_url_report(request.url, current_user)
    return {
        "status": "success",
        "message": "URL reported successfully",
        "url": request.url,
        "report_count": new_count,
    }
