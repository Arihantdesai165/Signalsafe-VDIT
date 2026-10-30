# -*- coding: utf-8 -*-
"""
SignalSafe Campus - JSON Data Migration Utility
Migrates data from legacy JSON files (incidents.json, stats.json, reports.json)
to the dedicated SignalSafe PostgreSQL database.

Features:
- Automated timestamped backup creation before migration.
- Record validation and schema sanitization.
- Concurrency-safe sequence adjustment post-import.
- Fully idempotent: safe to rerun without creating duplicate records.
- Comprehensive verification and tabular reporting.
"""

import os
import sys
import json
import shutil
import re
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

# Add workspace root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.database.connection import SessionLocal, check_db_connection
from backend.database.models import (
    UserProfile,
    IncidentReport,
    IncidentEvidence,
    IncidentInvestigation,
    SecurityAuditLog,
    CommunityReportedURL,
    AppStatistic,
)

DATA_DIR = os.path.join(BASE_DIR, "backend", "data")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
INCIDENTS_FILE = os.path.join(DATA_DIR, "incidents.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
REPORTS_FILE = os.path.join(DATA_DIR, "reports.json")


def create_backups() -> List[str]:
    """Creates a timestamped backup directory of all existing JSON persistence files."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backed_up = []

    for file_path in [INCIDENTS_FILE, STATS_FILE, REPORTS_FILE]:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            dest = os.path.join(BACKUP_DIR, f"{filename}.backup_{ts}")
            shutil.copy2(file_path, dest)
            backed_up.append(dest)

    return backed_up


def parse_iso_datetime(dt_str: Any) -> datetime:
    """Parses ISO timestamp string to timezone-aware UTC datetime."""
    if not dt_str or not isinstance(dt_str, str):
        return datetime.now(timezone.utc)
    try:
        # Handle Z suffix
        clean_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def migrate_stats(session: Session) -> Dict[str, Any]:
    """Migrates backend/data/stats.json to app_statistics table."""
    summary = {"total_read": 0, "inserted": 0, "updated": 0, "skipped": 0}
    if not os.path.exists(STATS_FILE):
        print("  -> stats.json not found: no historical stats data to migrate.")
        return summary

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            stats_data = json.load(f)
    except Exception as exc:
        print(f"[!] Warning: Could not read {STATS_FILE}: {exc}")
        return summary

    for key, val in stats_data.items():
        summary["total_read"] += 1
        try:
            int_val = int(val)
        except (ValueError, TypeError):
            summary["skipped"] += 1
            continue

        existing = session.query(AppStatistic).filter_by(stat_key=key).first()
        if existing:
            if existing.stat_value < int_val:
                existing.stat_value = int_val
                existing.updated_at = datetime.now(timezone.utc)
                summary["updated"] += 1
            else:
                summary["skipped"] += 1
        else:
            new_stat = AppStatistic(
                stat_key=key,
                stat_value=int_val,
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_stat)
            summary["inserted"] += 1

    return summary


def migrate_reports(session: Session) -> Dict[str, Any]:
    """Migrates backend/data/reports.json to community_reported_urls table."""
    summary = {"total_read": 0, "inserted": 0, "updated": 0, "skipped": 0}
    if not os.path.exists(REPORTS_FILE):
        print("  -> reports.json not found: no historical threat URL data to migrate.")
        return summary

    try:
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            reports_data = json.load(f)
    except Exception as exc:
        print(f"[!] Warning: Could not read {REPORTS_FILE}: {exc}")
        return summary

    for raw_url, count in reports_data.items():
        summary["total_read"] += 1
        url_clean = raw_url.strip().lower()
        if not url_clean:
            summary["skipped"] += 1
            continue

        try:
            report_cnt = int(count)
        except (ValueError, TypeError):
            report_cnt = 1

        existing = session.query(CommunityReportedURL).filter_by(url_key=url_clean).first()
        if existing:
            if existing.report_count < report_cnt:
                existing.report_count = report_cnt
                existing.last_reported_at = datetime.now(timezone.utc)
                summary["updated"] += 1
            else:
                summary["skipped"] += 1
        else:
            new_report = CommunityReportedURL(
                url_key=url_clean,
                report_count=report_cnt,
                last_reported_at=datetime.now(timezone.utc),
            )
            session.add(new_report)
            summary["inserted"] += 1

    return summary


def migrate_incidents(session: Session) -> Dict[str, Any]:
    """
    Migrates backend/data/incidents.json to incident_reports, incident_investigations,
    incident_evidence, security_audit_logs, and user_profiles.
    """
    summary = {
        "total_read": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "malformed": 0,
        "investigations_created": 0,
        "evidence_created": 0,
        "audit_logs_created": 0,
        "profiles_created": 0,
        "max_incident_number": 0,
    }

    if not os.path.exists(INCIDENTS_FILE):
        print("  -> incidents.json not found: no historical incident reports to migrate.")
        return summary

    try:
        with open(INCIDENTS_FILE, "r", encoding="utf-8") as f:
            incidents_data = json.load(f)
    except Exception as exc:
        print(f"[!] Error: Could not read {INCIDENTS_FILE}: {exc}")
        return summary

    if not isinstance(incidents_data, list):
        print(f"[!] Error: {INCIDENTS_FILE} does not contain a JSON list.")
        return summary

    for inc in incidents_data:
        summary["total_read"] += 1
        inc_id = inc.get("id")
        if not inc_id or not isinstance(inc_id, str):
            summary["malformed"] += 1
            continue

        # Extract number for sequence tracking
        match = re.search(r"(\d+)$", inc_id)
        if match:
            num = int(match.group(1))
            if num > summary["max_incident_number"]:
                summary["max_incident_number"] = num

        # Validate required fields
        reported_by = inc.get("reported_by") or "Anonymous User"
        category = inc.get("category") or "other"
        target_evidence = inc.get("target_evidence") or "None"
        description = inc.get("description") or "No description provided."
        status_val = inc.get("status") or "Pending"
        severity_val = inc.get("severity") or "Medium"
        created_at = parse_iso_datetime(inc.get("created_at"))
        updated_at = parse_iso_datetime(inc.get("updated_at") or inc.get("created_at"))

        # Derive / upsert user profile if email exists
        reporter_email = inc.get("reporter_email")
        reporter_role = inc.get("reporter_role") or "STUDENT"
        reporter_dept = inc.get("reporter_dept")

        if reporter_email:
            existing_user = session.query(UserProfile).filter_by(email=reporter_email).first()
            if not existing_user:
                erp_id = f"ERP-{reporter_email.split('@')[0].upper()}"
                new_profile = UserProfile(
                    erp_user_id=erp_id,
                    display_name=reported_by,
                    email=reporter_email,
                    role=reporter_role,
                    department=reporter_dept,
                    created_at=created_at,
                    updated_at=updated_at,
                )
                session.add(new_profile)
                session.flush()
                summary["profiles_created"] += 1

        # Check existing incident
        existing_inc = session.query(IncidentReport).filter_by(incident_id=inc_id).first()
        if existing_inc:
            # Update existing
            existing_inc.reported_by = reported_by
            existing_inc.reporter_email = reporter_email
            existing_inc.reporter_role = reporter_role
            existing_inc.reporter_dept = reporter_dept
            existing_inc.category = category
            existing_inc.category_label = inc.get("category_label")
            existing_inc.description = description
            existing_inc.target_evidence = target_evidence
            existing_inc.severity = severity_val
            existing_inc.status = status_val
            existing_inc.updated_at = updated_at
            report_obj = existing_inc
            summary["updated"] += 1
        else:
            report_obj = IncidentReport(
                incident_id=inc_id,
                reporter_erp_id=f"ERP-{reporter_email.split('@')[0].upper()}" if reporter_email else None,
                reported_by=reported_by,
                reporter_email=reporter_email,
                reporter_role=reporter_role,
                reporter_dept=reporter_dept,
                category=category,
                category_label=inc.get("category_label"),
                title=inc.get("title") or inc.get("category_label") or category,
                description=description,
                target_evidence=target_evidence,
                severity=severity_val,
                status=status_val,
                created_at=created_at,
                updated_at=updated_at,
            )
            session.add(report_obj)
            session.flush()
            summary["inserted"] += 1

        # Migrate evidence if target_evidence exists
        if target_evidence and target_evidence != "None":
            existing_evidence = session.query(IncidentEvidence).filter_by(
                incident_id=report_obj.id,
                evidence_type="target_evidence",
            ).first()
            if not existing_evidence:
                ev = IncidentEvidence(
                    incident_id=report_obj.id,
                    evidence_type="target_evidence",
                    file_storage_ref=None,
                    sanitized_metadata=json.dumps({"indicator": target_evidence}),
                    uploaded_by_erp_id=report_obj.reporter_erp_id,
                    created_at=created_at,
                )
                session.add(ev)
                summary["evidence_created"] += 1

        # Migrate notes -> incident_investigations
        notes = inc.get("notes", [])
        if isinstance(notes, list):
            for n in notes:
                n_text = n.get("text") or n.get("note") or ""
                if not n_text:
                    continue
                n_ts = parse_iso_datetime(n.get("timestamp") or n.get("created_at"))
                n_author = n.get("author") or "Campus CyberAdmin"

                # Check if this note already exists
                existing_inv = session.query(IncidentInvestigation).filter_by(
                    incident_id=report_obj.id,
                    investigation_note=n_text,
                ).first()
                if not existing_inv:
                    inv = IncidentInvestigation(
                        incident_id=report_obj.id,
                        admin_name=n_author,
                        action_type="NOTE_ADDED",
                        investigation_note=n_text,
                        previous_status=None,
                        new_status=status_val,
                        created_at=n_ts,
                    )
                    session.add(inv)
                    summary["investigations_created"] += 1

        # Migrate audit_trail -> incident_investigations + security_audit_logs
        audit_trail = inc.get("audit_trail", [])
        if isinstance(audit_trail, list):
            for a in audit_trail:
                a_action = a.get("action") or "Audit Event"
                a_by = a.get("by") or "System"
                a_ts = parse_iso_datetime(a.get("timestamp"))
                a_note = a.get("note") or a_action

                # Deterministic event key to prevent duplicate audit logs on rerun
                content_hash = hashlib.sha256(f"{inc_id}:{a_action}:{a_note}:{a_ts.isoformat()}".encode("utf-8")).hexdigest()[:12]
                event_key = f"MIG-{inc_id}-{a_ts.strftime('%Y%m%d%H%M%S')}-{content_hash}"
                existing_audit = session.query(SecurityAuditLog).filter_by(event_id=event_key).first()
                if not existing_audit:
                    audit_log = SecurityAuditLog(
                        event_id=event_key,
                        actor_name=a_by,
                        event_type="INCIDENT_AUDIT",
                        target_resource_type="incident",
                        target_resource_id=inc_id,
                        outcome="SUCCESS",
                        details=json.dumps({"action": a_action, "note": a_note}),
                        created_at=a_ts,
                    )
                    session.add(audit_log)
                    summary["audit_logs_created"] += 1

    return summary


def update_sequence(session: Session, max_num: int) -> int:
    """Updates the incident_id_seq PostgreSQL sequence so future inserts never collide."""
    db_max = 0
    all_ids = session.query(IncidentReport.incident_id).all()
    for (inc_id,) in all_ids:
        match = re.search(r"(\d+)$", str(inc_id))
        if match:
            num = int(match.group(1))
            if num > db_max:
                db_max = num

    overall_max = max(max_num, db_max, 1)
    target_val = overall_max + 1
    session.execute(text(f"SELECT setval('incident_id_seq', {target_val}, false)"))
    session.commit()
    return target_val


def run_migration() -> bool:
    """Main execution orchestrator for JSON migration."""
    print("=" * 70)
    print("   SIGNALSAFE CAMPUS - JSON TO POSTGRESQL DATA MIGRATION")
    print("=" * 70)

    # 1. Verify DB Connectivity
    if not check_db_connection():
        print("[!] ERROR: Unable to connect to SignalSafe PostgreSQL database.")
        print("    Ensure the Docker container 'signalsafe_postgres' is running.")
        return False

    # 2. Back up existing files
    print("\n[1/5] Backing up JSON files...")
    backups = create_backups()
    for b in backups:
        print(f"  -> Created backup: {b}")

    # 3. Migrate data within session
    session = SessionLocal()
    try:
        print("\n[2/5] Migrating app statistics (stats.json)...")
        stats_summary = migrate_stats(session)
        session.commit()
        print(f"  -> Inserted: {stats_summary['inserted']}, Updated: {stats_summary['updated']}, Skipped: {stats_summary['skipped']}")

        print("\n[3/5] Migrating community reported URLs (reports.json)...")
        reports_summary = migrate_reports(session)
        session.commit()
        print(f"  -> Inserted: {reports_summary['inserted']}, Updated: {reports_summary['updated']}, Skipped: {reports_summary['skipped']}")

        print("\n[4/5] Migrating incident reports and investigation history (incidents.json)...")
        inc_summary = migrate_incidents(session)
        session.commit()
        print(f"  -> Incidents: {inc_summary['inserted']} inserted, {inc_summary['updated']} updated, {inc_summary['skipped']} skipped")
        print(f"  -> Evidence items created: {inc_summary['evidence_created']}")
        print(f"  -> Investigation notes created: {inc_summary['investigations_created']}")
        print(f"  -> Security audit logs created: {inc_summary['audit_logs_created']}")
        print(f"  -> User profiles created: {inc_summary['profiles_created']}")

        print("\n[5/5] Aligning PostgreSQL incident_id_seq sequence...")
        next_seq = update_sequence(session, inc_summary["max_incident_number"])
        print(f"  -> incident_id_seq successfully advanced to: {next_seq}")

        # Post-migration verification
        total_incidents = session.query(IncidentReport).count()
        total_evidence = session.query(IncidentEvidence).count()
        total_investigations = session.query(IncidentInvestigation).count()
        total_audit_logs = session.query(SecurityAuditLog).count()
        total_urls = session.query(CommunityReportedURL).count()
        total_stats = session.query(AppStatistic).count()

        print("\n" + "=" * 70)
        print("   MIGRATION VERIFICATION & SUMMARY TABLE")
        print("=" * 70)
        print(f"  {'Entity':<32} | {'Count in PostgreSQL':<20}")
        print("  " + "-" * 55)
        print(f"  {'Incident Reports':<32} | {total_incidents:<20}")
        print(f"  {'Incident Evidence Items':<32} | {total_evidence:<20}")
        print(f"  {'Investigation History Records':<32} | {total_investigations:<20}")
        print(f"  {'Security Audit Logs':<32} | {total_audit_logs:<20}")
        print(f"  {'Community Reported URLs':<32} | {total_urls:<20}")
        print(f"  {'App Statistics Keys':<32} | {total_stats:<20}")
        print("=" * 70)
        print("   MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        return True

    except Exception as exc:
        session.rollback()
        print(f"\n[!] Migration failed with error: {exc}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
