# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Normalized SQLAlchemy Database Models
Includes models for User Profiles, Incidents, Evidence, Investigations,
Screenshot Scans, URL Scans, QR Scans, Security Audit Logs, User Preferences,
and Community Reported Threat Counters.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Float,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Sequence,
    Index,
)
from sqlalchemy.orm import relationship
from .connection import Base

# Concurrency-safe sequence for unique Incident IDs (e.g. INC-2026-0001)
incident_id_seq = Sequence("incident_id_seq", start=1, increment=1)


class UserProfile(Base):
    """
    Minimal SignalSafe user profile synchronized from trusted JCER ERP identity.
    Does NOT store passwords, tokens, or credentials.
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    erp_user_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    role = Column(String(50), nullable=False, default="STUDENT")
    department = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    preferences = relationship("UserPreference", back_populates="user_profile", uselist=False, cascade="all, delete-orphan")


class IncidentReport(Base):
    """
    Persistent cybersecurity incident reports submitted by students, faculty, or admins.
    Uses concurrency-safe sequence generation for unique incident IDs.
    """
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(50), unique=True, nullable=False, index=True)
    reporter_erp_id = Column(String(100), nullable=True, index=True)
    reported_by = Column(String(255), nullable=False)
    reporter_email = Column(String(255), nullable=True)
    reporter_role = Column(String(50), nullable=False, default="STUDENT")
    reporter_dept = Column(String(255), nullable=True)

    category = Column(String(100), nullable=False)
    category_label = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    target_evidence = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, default="Medium")
    status = Column(String(50), nullable=False, default="Pending", index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    assigned_admin_erp_id = Column(String(100), nullable=True, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    evidence = relationship(
        "IncidentEvidence",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentEvidence.created_at.asc()",
    )
    investigations = relationship(
        "IncidentInvestigation",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentInvestigation.created_at.asc()",
    )


class IncidentEvidence(Base):
    """Metadata references for evidence associated with an incident."""
    __tablename__ = "incident_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incident_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(50), nullable=False)  # url, upi_qr, screenshot, text, file
    file_storage_ref = Column(String(500), nullable=True)
    sanitized_metadata = Column(Text, nullable=True)  # JSON-encoded sanitized metadata
    uploaded_by_erp_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("IncidentReport", back_populates="evidence")


class IncidentInvestigation(Base):
    """Chronological investigation actions and notes added by CyberAdmin."""
    __tablename__ = "incident_investigations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(Integer, ForeignKey("incident_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    admin_erp_id = Column(String(100), nullable=True)
    admin_name = Column(String(255), nullable=False)
    action_type = Column(String(100), nullable=False)  # STATUS_CHANGE, NOTE_ADDED, REPORT_SUBMITTED
    investigation_note = Column(Text, nullable=False)
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident = relationship("IncidentReport", back_populates="investigations")


class ScreenshotScanResult(Base):
    """Persistent scan result for UPI payment screenshot OCR and fraud classification."""
    __tablename__ = "screenshot_scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(64), unique=True, nullable=False, index=True)
    user_erp_id = Column(String(100), nullable=True, index=True)
    detection_result = Column(String(100), nullable=False)
    risk_score = Column(Float, nullable=False)
    detection_metadata = Column(Text, nullable=True)  # JSON-encoded extracted fields, reasons
    engine_version = Column(String(50), default="SignalSafe-OCR-v2.0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class URLScanResult(Base):
    """Persistent scan result for URL and website phishing analysis."""
    __tablename__ = "url_scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(64), unique=True, nullable=False, index=True)
    user_erp_id = Column(String(100), nullable=True, index=True)
    normalized_url = Column(Text, nullable=False)
    detection_result = Column(String(100), nullable=False)
    risk_score = Column(Float, nullable=False)
    detection_metadata = Column(Text, nullable=True)  # JSON-encoded reasons, indicators
    report_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class QRScanResult(Base):
    """Persistent scan result for UPI QR code decoding and fraud checks."""
    __tablename__ = "qr_scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String(64), unique=True, nullable=False, index=True)
    user_erp_id = Column(String(100), nullable=True, index=True)
    extracted_destination = Column(Text, nullable=False)
    detection_result = Column(String(100), nullable=False)
    risk_score = Column(Float, nullable=False)
    detection_metadata = Column(Text, nullable=True)  # JSON-encoded UPI parameters, payee name
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class SecurityAuditLog(Base):
    """
    Immutable security audit trail for privileged operations, status changes,
    unauthorized attempts, and security events. Never logs credentials.
    """
    __tablename__ = "security_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    actor_erp_id = Column(String(100), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_role = Column(String(50), nullable=True)
    event_type = Column(String(100), nullable=False, index=True)
    target_resource_type = Column(String(100), nullable=False)
    target_resource_id = Column(String(100), nullable=True)
    outcome = Column(String(50), nullable=False, default="SUCCESS")
    details = Column(Text, nullable=True)  # JSON-encoded safe event metadata
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class UserPreference(Base):
    """Lightweight user preference settings for the SignalSafe portal."""
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_erp_id = Column(String(100), ForeignKey("user_profiles.erp_user_id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    language = Column(String(10), default="en", nullable=False)
    theme = Column(String(20), default="light", nullable=False)
    email_notifications = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user_profile = relationship("UserProfile", back_populates="preferences")


class CommunityReportedURL(Base):
    """Community-reported malicious or suspicious URLs with report counts."""
    __tablename__ = "community_reported_urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url_key = Column(Text, unique=True, nullable=False, index=True)
    report_count = Column(Integer, default=1, nullable=False)
    last_reported_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class AppStatistic(Base):
    """Persistent key-value counters (e.g. screenshots_analyzed)."""
    __tablename__ = "app_statistics"

    stat_key = Column(String(100), primary_key=True)
    stat_value = Column(BigInteger, default=0, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ScreenshotDataset(Base):
    """
    Metadata and versioning for CyberAdmin-uploaded reference transaction datasets
    used by the dataset-driven Screenshot Detector.
    """
    __tablename__ = "screenshot_datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    dataset_name = Column(String(255), nullable=False)
    dataset_type = Column(String(100), default="Demonstration Synthetic Dataset", nullable=False)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    total_records = Column(Integer, default=0, nullable=False)
    valid_records = Column(Integer, default=0, nullable=False)
    invalid_records = Column(Integer, default=0, nullable=False)
    uploaded_by_erp_id = Column(String(100), nullable=True)
    uploaded_by_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)

    records = relationship("ScreenshotTransactionRecord", back_populates="dataset", cascade="all, delete-orphan")


class ScreenshotTransactionRecord(Base):
    """
    Individual transaction references imported from a CyberAdmin CSV dataset.
    Provides reference matching for UPI payments without prefix-based heuristics.
    """
    __tablename__ = "screenshot_transaction_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(Integer, ForeignKey("screenshot_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    record_id = Column(String(100), nullable=True, index=True)
    transaction_id = Column(String(100), nullable=True, index=True)
    utr_rrn = Column(String(100), nullable=True, index=True)
    transaction_date = Column(String(50), nullable=True)
    transaction_time = Column(String(50), nullable=True)
    amount_inr = Column(Float, nullable=True, index=True)
    currency = Column(String(10), default="INR", nullable=False)
    payer_display_name = Column(String(255), nullable=True)
    payer_account_masked = Column(String(100), nullable=True)
    payee_name = Column(String(255), nullable=True, index=True)
    payee_vpa = Column(String(255), nullable=True, index=True)
    bank_or_app_label = Column(String(100), nullable=True)
    transaction_status = Column(String(50), nullable=True)
    dataset_type = Column(String(100), nullable=True)
    verification_status = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    dataset = relationship("ScreenshotDataset", back_populates="records")


class CollegePaymentQR(Base):
    """
    Authoritative registry of official JCER College payment QR codes
    managed and approved by CyberAdmin.
    Provides verified reference destinations for the QR Code Security Scanner.
    """
    __tablename__ = "college_payment_qrs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    payment_purpose = Column(String(100), nullable=False, index=True)
    department = Column(String(150), nullable=True, index=True)
    official_recipient_name = Column(String(255), nullable=False, index=True)
    expected_upi_id = Column(String(255), nullable=False, index=True)
    expected_amount = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    merchant_code = Column(String(50), nullable=True)
    qr_payload = Column(Text, nullable=False)
    payload_fingerprint = Column(String(64), nullable=False, index=True)
    image_storage_ref = Column(String(255), nullable=True)
    approval_status = Column(String(50), default="PENDING_APPROVAL", nullable=False, index=True)
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    created_by_erp_id = Column(String(100), nullable=True)
    created_by_name = Column(String(255), nullable=True)
    approved_by_erp_id = Column(String(100), nullable=True)
    approved_by_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_college_qr_lookup", "payload_fingerprint", "is_active", "approval_status"),
        Index("idx_college_qr_vpa_lookup", "expected_upi_id", "is_active", "approval_status"),
    )


