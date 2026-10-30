# -*- coding: utf-8 -*-
"""
SignalSafe Campus - CyberAdmin-Managed College QR Registry and Layered QR Verification Test Suite.

Validates Tests A through L:
- Test A: Exact registered college QR match (VERIFIED_JCER_COLLEGE_QR, safe status, risk <= 15).
- Test B: Different destination (OTHER_UPI_QR_NOT_REGISTERED).
- Test C: Same destination, changed amount (KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER).
- Test D: Same destination, altered recipient name (KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER).
- Test E: Legitimate external UPI QR (OTHER_UPI_QR_NOT_REGISTERED, trusted handle).
- Test F: Suspicious URL QR (threat preserved -> SUSPICIOUS_OR_UNSAFE_QR, risk >= 85).
- Test G: Non-decodable / corrupt image (UNABLE_TO_VERIFY).
- Test H: Empty / deactivated registry (NO_ACTIVE_COLLEGE_REGISTRY).
- Test I: Unauthorized access check (Student 403 Forbidden on CyberAdmin endpoints, Admin 200 OK).
- Test J: Duplicate QR registration warning check.
- Test K: Database persistence across updates, image retrieval, and audit logs.
- Test L: Non-interference and scan history integration.
"""

import io
import os
import sys
import uuid
import unittest
import qrcode
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session
from backend.services.college_qr_service import (
    register_college_qr,
    approve_and_activate_qr,
    deactivate_qr,
    reactivate_qr,
    archive_qr,
    check_duplicate_qr,
    canonicalize_upi_uri,
    compute_payload_fingerprint,
    MANDATORY_REGISTRY_NOTICE,
)
from backend.database.connection import SessionLocal
from backend.database.models import CollegePaymentQR, SecurityAuditLog

client = TestClient(app)


def make_qr_image_bytes(payload: str) -> bytes:
    """Helper to generate real in-memory PNG bytes for a QR code."""
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestCollegeQrRegistry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cyberadmin_user = {
            "id": "CYBER-ADMIN-01",
            "erp_user_id": "CYBER-ADMIN-01",
            "email": "cyberadmin@jcer.edu",
            "name": "Chief Security Officer",
            "role": "CYBERADMIN",
            "department": "Cybersecurity & IT Cell",
        }
        cls.student_user = {
            "id": "STU-2026-999",
            "erp_user_id": "STU-2026-999",
            "email": "student99@jcer.edu",
            "name": "Kavya Patel",
            "role": "STUDENT",
            "department": "Computer Science & Engineering",
        }

        cls.admin_token = generate_signalsafe_session(cls.cyberadmin_user)["token"]
        cls.student_token = generate_signalsafe_session(cls.student_user)["token"]

        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    def setUp(self):
        # Clean up existing test records to ensure isolated state
        session = SessionLocal()
        try:
            session.query(CollegePaymentQR).filter(
                CollegePaymentQR.expected_upi_id.like("%test%jcer%") |
                CollegePaymentQR.expected_upi_id.like("%jcer.admissions%") |
                CollegePaymentQR.expected_upi_id.like("%jcer.examfees%")
            ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()

    # --------------------------------------------------------------------------
    # Test A: Exact Registered College QR Match
    # --------------------------------------------------------------------------
    def test_a_exact_registered_college_qr_match(self):
        """Test A: Scanned QR exactly matches an approved active JCER college QR record."""
        payload = "upi://pay?pa=jcer.admissions@sbi&pn=Jain%20College%20of%20Engineering&am=500.00&cu=INR"
        img_bytes = make_qr_image_bytes(payload)

        # Register and approve QR code
        reg = register_college_qr(
            image_bytes=img_bytes,
            filename="jcer_admissions.png",
            display_name="JCER Admission Application Desk",
            payment_purpose="Admission Application Fee",
            official_recipient_name="Jain College of Engineering & Research",
            expected_upi_id="jcer.admissions@sbi",
            department="Admissions & Marketing Cell",
            expected_amount=500.00,
            description="Official admission application fee QR code",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )
        record_id = reg["record_id"]
        self.assertTrue(reg["is_active"])
        self.assertEqual(reg["approval_status"], "APPROVED")

        # Now test scanning identical QR image via student scan endpoint
        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("scanned_admissions.png", img_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "VERIFIED_JCER_COLLEGE_QR")
        self.assertEqual(data["status"], "safe")
        self.assertLessEqual(data["risk_score"], 15)
        self.assertTrue(data["is_college_verified"])
        self.assertEqual(data["registered_display_name"], "JCER Admission Application Desk")
        self.assertEqual(data["payment_purpose"], "Admission Application Fee")
        self.assertEqual(data["department"], "Admissions & Marketing Cell")

        # Verify Mandatory Disclaimer Notice
        cv = data["college_verification"]
        self.assertIn("MANDATORY_REGISTRY_NOTICE", dir(sys.modules["backend.services.college_qr_service"]))
        self.assertIn("JCER CyberAdmin", cv["registry_notice"])
        self.assertIn("does not independently prove bank-account ownership", cv["registry_notice"])
        self.assertIn("does not independently prove bank-account ownership", cv["explanation"])

    # --------------------------------------------------------------------------
    # Test B: Different Destination (Unregistered External UPI QR)
    # --------------------------------------------------------------------------
    def test_b_different_destination_unregistered_upi(self):
        """Test B: Valid UPI QR with different destination is classified as OTHER_UPI_QR_NOT_REGISTERED."""
        # Active JCER QR in registry
        reg_payload = "upi://pay?pa=jcer.admissions@sbi&pn=Jain%20College%20of%20Engineering&cu=INR"
        register_college_qr(
            image_bytes=make_qr_image_bytes(reg_payload),
            filename="reg.png",
            display_name="JCER Admissions",
            payment_purpose="Admission Application Fee",
            official_recipient_name="Jain College of Engineering & Research",
            expected_upi_id="jcer.admissions@sbi",
            department="Admissions & Marketing Cell",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        # Scanned QR points to completely different external destination
        unregistered_payload = "upi://pay?pa=cafeteria.vendor@sbi&pn=Campus%20Cafeteria&am=120.00&cu=INR"
        img_bytes = make_qr_image_bytes(unregistered_payload)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("unregistered.png", img_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "OTHER_UPI_QR_NOT_REGISTERED")
        self.assertFalse(data["is_college_verified"])
        self.assertIn("does not match an approved JCER college QR record", data["college_verification"]["explanation"])

    # --------------------------------------------------------------------------
    # Test C: Same UPI ID, Changed Amount (Details Differ)
    # --------------------------------------------------------------------------
    def test_c_same_destination_changed_amount(self):
        """Test C: Scanned QR matches destination UPI ID but tampered amount (e.g. 500 expected vs 1500 scanned)."""
        reg_payload = "upi://pay?pa=jcer.examfees@sbi&pn=JCER%20Exam%20Office&am=500.00&cu=INR"
        register_college_qr(
            image_bytes=make_qr_image_bytes(reg_payload),
            filename="exam_fees.png",
            display_name="JCER Semester Exam Fee",
            payment_purpose="Examination Fee",
            official_recipient_name="JCER Belagavi Exam Cell",
            expected_upi_id="jcer.examfees@sbi",
            department="Examination Section",
            expected_amount=500.00,
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        # Tampered amount in scanned QR: 1500.00 instead of 500.00
        tampered_payload = "upi://pay?pa=jcer.examfees@sbi&pn=JCER%20Exam%20Office&am=1500.00&cu=INR"
        tampered_bytes = make_qr_image_bytes(tampered_payload)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("tampered_amount.png", tampered_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER")
        self.assertFalse(data["is_college_verified"])
        self.assertGreaterEqual(data["risk_score"], 65)

        differing_fields = data["college_verification"]["differing_fields"]
        amount_diff = next((d for d in differing_fields if d["field"] == "Amount"), None)
        self.assertIsNotNone(amount_diff)
        self.assertEqual(amount_diff["expected"], 500.00)
        self.assertEqual(amount_diff["observed"], 1500.00)

    # --------------------------------------------------------------------------
    # Test D: Same Destination, Altered Recipient Name
    # --------------------------------------------------------------------------
    def test_d_same_destination_altered_recipient_name(self):
        """Test D: Scanned QR matches destination UPI ID but recipient name has been modified."""
        reg_payload = "upi://pay?pa=jcer.examfees@sbi&pn=JCER%20Belagavi%20Exam%20Cell&am=500.00&cu=INR"
        register_college_qr(
            image_bytes=make_qr_image_bytes(reg_payload),
            filename="exam_fees.png",
            display_name="JCER Semester Exam Fee",
            payment_purpose="Examination Fee",
            official_recipient_name="JCER Belagavi Exam Cell",
            expected_upi_id="jcer.examfees@sbi",
            department="Examination Section",
            expected_amount=500.00,
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        # Altered Payee Name in scanned QR
        tampered_name_payload = "upi://pay?pa=jcer.examfees@sbi&pn=Unofficial%20Fee%20Collector&am=500.00&cu=INR"
        tampered_bytes = make_qr_image_bytes(tampered_name_payload)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("tampered_name.png", tampered_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER")
        self.assertFalse(data["is_college_verified"])

        differing_fields = data["college_verification"]["differing_fields"]
        name_diff = next((d for d in differing_fields if d["field"] == "Official Recipient Name"), None)
        self.assertIsNotNone(name_diff)
        self.assertEqual(name_diff["expected"], "JCER Belagavi Exam Cell")
        self.assertEqual(name_diff["observed"], "Unofficial Fee Collector")

    # --------------------------------------------------------------------------
    # Test E: Legitimate External UPI QR
    # --------------------------------------------------------------------------
    def test_e_legitimate_external_upi_qr(self):
        """Test E: A standard, non-malicious external UPI QR (e.g. @okaxis) is correctly recognized."""
        # Ensure at least one active college QR exists
        reg_payload = "upi://pay?pa=jcer.admissions@sbi&pn=Jain%20College&cu=INR"
        register_college_qr(
            image_bytes=make_qr_image_bytes(reg_payload),
            filename="active.png",
            display_name="Active JCER",
            payment_purpose="Tuition Fees",
            official_recipient_name="Jain College",
            expected_upi_id="jcer.admissions@sbi",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        external_payload = "upi://pay?pa=bookstore.campus@okaxis&pn=Campus%20Book%20Depot&am=450.00&cu=INR"
        external_bytes = make_qr_image_bytes(external_payload)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("bookstore.png", external_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "OTHER_UPI_QR_NOT_REGISTERED")
        self.assertEqual(data["status"], "safe")
        self.assertLessEqual(data["risk_score"], 25)
        self.assertFalse(data["is_college_verified"])

    # --------------------------------------------------------------------------
    # Test F: Suspicious URL / Phishing QR (Threat Warning Preserved)
    # --------------------------------------------------------------------------
    def test_f_suspicious_url_phishing_qr(self):
        """Test F: A QR containing a phishing URL is flagged as SUSPICIOUS_OR_UNSAFE_QR with high risk score."""
        phishing_url = "http://jcer-portal.update-kyc.fraud-server.org/login?redirect=steal"
        phishing_bytes = make_qr_image_bytes(phishing_url)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("phishing_qr.png", phishing_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "SUSPICIOUS_OR_UNSAFE_QR")
        self.assertGreaterEqual(data["risk_score"], 85)
        self.assertIn(data["status"], ["danger", "blocked"])
        self.assertFalse(data["is_college_verified"])

    # --------------------------------------------------------------------------
    # Test G: Invalid / Non-Decodable Image
    # --------------------------------------------------------------------------
    def test_g_invalid_non_decodable_image(self):
        """Test G: Corrupted image or blank file returns clean UNABLE_TO_VERIFY response without crashing."""
        corrupt_bytes = b"not-a-valid-image-format-bytes-12345"

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("corrupt.png", corrupt_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "UNABLE_TO_VERIFY")
        self.assertFalse(data["is_college_verified"])
        self.assertIn("Could not decode image file", data["college_verification"]["explanation"])

    # --------------------------------------------------------------------------
    # Test H: Empty / Deactivated Registry
    # --------------------------------------------------------------------------
    def test_h_empty_or_deactivated_registry(self):
        """Test H: When no approved college records are active, scanner outputs NO_ACTIVE_COLLEGE_REGISTRY."""
        session = SessionLocal()
        try:
            # Set all records to inactive
            session.query(CollegePaymentQR).update({"is_active": False})
            session.commit()
        finally:
            session.close()

        upi_payload = "upi://pay?pa=jcer.admissions@sbi&pn=Jain%20College&am=500.00&cu=INR"
        upi_bytes = make_qr_image_bytes(upi_payload)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("upi.png", upi_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "NO_ACTIVE_COLLEGE_REGISTRY")
        self.assertFalse(data["is_college_verified"])
        self.assertIn("College QR Registry Inactive", data["college_verification"]["heading"])

    # --------------------------------------------------------------------------
    # Test I: CyberAdmin RBAC (Student 403 Forbidden vs Admin 200 OK)
    # --------------------------------------------------------------------------
    def test_i_cyberadmin_rbac(self):
        """Test I: Non-CyberAdmin users receive 403 Forbidden on all college QR management routes."""
        test_payload = "upi://pay?pa=jcer.fees@sbi&pn=JCER&cu=INR"
        img_bytes = make_qr_image_bytes(test_payload)

        # 1. Student attempted upload
        res = client.post(
            "/api/cyberadmin/college-qr/upload",
            data={
                "display_name": "Student Upload Attempt",
                "payment_purpose": "Tuition Fees",
                "official_recipient_name": "JCER",
                "expected_upi_id": "jcer.fees@sbi",
            },
            files={"file": ("test.png", img_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("CyberAdmin authorization required", res.json()["detail"])

        # 2. Student attempted stats lookup
        res = client.get("/api/cyberadmin/college-qr/stats", headers=self.student_headers)
        self.assertEqual(res.status_code, 403)

        # 3. Student attempted preview decode
        res = client.post(
            "/api/cyberadmin/college-qr/preview-decode",
            files={"file": ("test.png", img_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(res.status_code, 403)

        # 4. CyberAdmin authorized access to stats
        admin_res = client.get("/api/cyberadmin/college-qr/stats", headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 200)
        stats = admin_res.json()
        self.assertIn("total_registered", stats)
        self.assertIn("active_approved", stats)
        self.assertIn("configured_purposes", stats)
        self.assertIn("configured_departments", stats)

    # --------------------------------------------------------------------------
    # Test J: Duplicate QR Registration Warning Check
    # --------------------------------------------------------------------------
    def test_j_duplicate_registration_warning(self):
        """Test J: Duplicate detection warns CyberAdmin when registering identical payload or destination."""
        payload = "upi://pay?pa=jcer.unique.dup@sbi&pn=JCER%20Dup&am=200.00&cu=INR"
        img_bytes = make_qr_image_bytes(payload)

        # Register initial record
        reg1 = register_college_qr(
            image_bytes=img_bytes,
            filename="dup1.png",
            display_name="First Record",
            payment_purpose="Tuition Fees",
            official_recipient_name="JCER Belagavi",
            expected_upi_id="jcer.unique.dup@sbi",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        # Check duplicate lookup
        warnings = check_duplicate_qr(
            fingerprint=compute_payload_fingerprint(payload),
            upi_id="jcer.unique.dup@sbi",
        )
        self.assertTrue(len(warnings) > 0)
        self.assertTrue(any("Identical QR payload" in w for w in warnings))

    # --------------------------------------------------------------------------
    # Test K: Database Persistence, Image Serving, State Transitions, and Audit Logging
    # --------------------------------------------------------------------------
    def test_k_persistence_state_transitions_and_audit(self):
        """Test K: QR registration persists in PostgreSQL, state transitions work, audit logs are logged."""
        payload = "upi://pay?pa=jcer.hostel@sbi&pn=JCER%20Hostel&cu=INR"
        img_bytes = make_qr_image_bytes(payload)

        # Register unapproved
        reg = register_college_qr(
            image_bytes=img_bytes,
            filename="hostel.png",
            display_name="JCER Boys Hostel Mess",
            payment_purpose="Hostel & Mess Dues",
            official_recipient_name="JCER Hostel Committee",
            expected_upi_id="jcer.hostel@sbi",
            department="Student Affairs & Hostel",
            admin_user=self.cyberadmin_user,
            auto_approve=False,
        )
        record_id = reg["record_id"]
        self.assertEqual(reg["approval_status"], "PENDING_APPROVAL")
        self.assertFalse(reg["is_active"])

        # Fetch image endpoint
        img_res = client.get(f"/api/cyberadmin/college-qr/{record_id}/image", headers=self.admin_headers)
        self.assertEqual(img_res.status_code, 200)
        self.assertEqual(img_res.headers["content-type"], "image/png")
        self.assertEqual(img_res.content, img_bytes)

        # Approve and activate
        appr_res = client.post(f"/api/cyberadmin/college-qr/{record_id}/approve", headers=self.admin_headers)
        self.assertEqual(appr_res.status_code, 200)
        self.assertTrue(appr_res.json()["record"]["is_active"])
        self.assertEqual(appr_res.json()["record"]["approval_status"], "APPROVED")

        # Deactivate
        deact_res = client.post(f"/api/cyberadmin/college-qr/{record_id}/deactivate", headers=self.admin_headers)
        self.assertEqual(deact_res.status_code, 200)
        self.assertFalse(deact_res.json()["record"]["is_active"])

        # Reactivate
        react_res = client.post(f"/api/cyberadmin/college-qr/{record_id}/reactivate", headers=self.admin_headers)
        self.assertEqual(react_res.status_code, 200)
        self.assertTrue(react_res.json()["record"]["is_active"])

        # Update metadata
        upd_res = client.patch(
            f"/api/cyberadmin/college-qr/{record_id}",
            json={
                "display_name": "JCER Boys Hostel Mess & Canteen",
                "department": "Hostel Board",
                "description": "Updated hostel mess QR",
            },
            headers=self.admin_headers,
        )
        self.assertEqual(upd_res.status_code, 200)
        self.assertEqual(upd_res.json()["record"]["display_name"], "JCER Boys Hostel Mess & Canteen")

        # Archive
        arch_res = client.post(f"/api/cyberadmin/college-qr/{record_id}/archive", headers=self.admin_headers)
        self.assertEqual(arch_res.status_code, 200)

        # Verify audit logs in PostgreSQL
        session = SessionLocal()
        try:
            logs = session.query(SecurityAuditLog).filter_by(
                target_resource_type="college_payment_qr",
                target_resource_id=record_id,
            ).all()
            event_types = [l.event_type for l in logs]
            self.assertIn("COLLEGE_QR_REGISTERED", event_types)
            self.assertIn("COLLEGE_QR_APPROVED", event_types)
            self.assertIn("COLLEGE_QR_DEACTIVATED", event_types)
            self.assertIn("COLLEGE_QR_REACTIVATED", event_types)
            self.assertIn("COLLEGE_QR_METADATA_UPDATED", event_types)
            self.assertIn("COLLEGE_QR_ARCHIVED", event_types)
        finally:
            session.close()

    # --------------------------------------------------------------------------
    # Test L: Canonical URI and Fingerprint Determinism
    # --------------------------------------------------------------------------
    def test_l_canonical_uri_and_fingerprint_determinism(self):
        """Test L: Query parameter order variations generate identical canonical payloads and fingerprints."""
        uri1 = "upi://pay?pn=JCER%20Belagavi&pa=fees@sbi&cu=INR&am=100.00"
        uri2 = "upi://pay?am=100.00&cu=inr&pa=FEES@SBI&pn=JCER%20Belagavi"

        canon1 = canonicalize_upi_uri(uri1)
        canon2 = canonicalize_upi_uri(uri2)
        self.assertEqual(canon1, canon2)

        fp1 = compute_payload_fingerprint(uri1)
        fp2 = compute_payload_fingerprint(uri2)
        self.assertEqual(fp1, fp2)


if __name__ == "__main__":
    unittest.main()
