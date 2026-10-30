# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Dark-Theme UPI QR Decoding and JCER Registry Verification Test Suite.

Validates:
- Test 1: Light-theme QR decoding and accurate field extraction (p1.jpeg, p2.jpeg).
- Test 2: Dark-theme QR decoding (prmod QR code real.jpeg - formerly failing, now working).
- Test 3: Stylized PhonePe QR with center logo decoding (realqryuvaraj.jpeg).
- Test 4: Result A: Official JCER QR Verified (VERIFIED_JCER_COLLEGE_QR, safe status, risk <= 15).
- Test 5: Result B: Valid External UPI QR (OTHER_UPI_QR_NOT_REGISTERED, safe status, risk <= 20, not fake).
- Test 6: Result C: Known College Recipient - Details Differ (KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER, risk 65).
- Test 7: Result D: Decoding Failed / Unreadable (status insufficient_evidence, risk 0, actionable guidance).
- Test 8: Phishing / Non-UPI URL threat detection preserved (risk >= 85).
- Test 9: Deactivated registry record is not matched as active.
- Test 10: Accurate parameter extraction with URL unquoting (spaces, amount, aid, mode, purpose).
- Test 11: CyberAdmin decode-preview and registry management with dark-theme QR.
- Test 12: Diagnostic reporting (theme detection, pass name, execution time).
"""

import io
import os
import sys
import uuid
import unittest
import numpy as np
import cv2
import qrcode
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session
from backend.services.college_qr_service import (
    register_college_qr,
    approve_and_activate_qr,
    deactivate_qr,
    canonicalize_upi_uri,
    compute_payload_fingerprint,
    MANDATORY_REGISTRY_NOTICE,
)
from backend.services.qrcode_service import (
    _decode_qr_multi_pass,
    _parse_upi_uri,
    _is_dark_background,
    analyze_qrcode,
)
from backend.database.connection import SessionLocal
from backend.database.models import CollegePaymentQR

client = TestClient(app)


def make_qr_png_bytes(payload: str, inverted: bool = False) -> bytes:
    """Helper to generate in-memory PNG bytes for light or dark theme QR codes."""
    qr = qrcode.QRCode(box_size=10, border=3)
    qr.add_data(payload)
    qr.make(fit=True)
    if inverted:
        # Dark theme: white modules on black background
        img = qr.make_image(fill_color="white", back_color="black")
    else:
        # Light theme: black modules on white background
        img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestDarkThemeQrAndRegistry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cyberadmin_user = {
            "id": "CYBER-ADMIN-TEST",
            "erp_user_id": "CYBER-ADMIN-TEST",
            "email": "cyberadmin@jcer.edu",
            "name": "Chief Security Officer",
            "role": "CYBERADMIN",
            "department": "Cybersecurity & IT Cell",
        }
        cls.student_user = {
            "id": "STU-TEST-001",
            "erp_user_id": "STU-TEST-001",
            "email": "student@jcer.edu",
            "name": "Student Tester",
            "role": "STUDENT",
            "department": "Computer Science & Engineering",
        }

        cls.admin_token = generate_signalsafe_session(cls.cyberadmin_user)["token"]
        cls.student_token = generate_signalsafe_session(cls.student_user)["token"]

        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    def setUp(self):
        # Clean up test records
        session = SessionLocal()
        try:
            session.query(CollegePaymentQR).filter(
                CollegePaymentQR.expected_upi_id.like("%test%dark%") |
                CollegePaymentQR.expected_upi_id.like("%jcer.dark%") |
                CollegePaymentQR.expected_upi_id.like("%jcer.examfees%")
            ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()

    # --------------------------------------------------------------------------
    # Test 1: Light-Theme QR Decoding
    # --------------------------------------------------------------------------
    def test_01_light_theme_qr_decoding(self):
        """Test 1: Standard light-theme QR images decode successfully with accurate parameters."""
        p1_path = os.path.join("datasets", "qr", "safe", "p1.jpeg")
        if os.path.exists(p1_path):
            with open(p1_path, "rb") as f:
                img_bytes = f.read()
            res = analyze_qrcode(img_bytes)
            self.assertEqual(res["status"], "safe")
            self.assertLessEqual(res["risk_score"], 20)
            self.assertEqual(res["classification"], "OTHER_UPI_QR_NOT_REGISTERED")
            self.assertEqual(res["payment_to"], "8105791108-3@ibl")
            self.assertEqual(res["payee_name"], "ARIHANT DESAI")
            self.assertFalse(res["diagnostics"]["is_dark_theme"])

    # --------------------------------------------------------------------------
    # Test 2: Dark-Theme QR Decoding (Formerly Failing)
    # --------------------------------------------------------------------------
    def test_02_dark_theme_qr_decoding(self):
        """Test 2: Dark-theme QR image (prmod QR code real.jpeg) decodes cleanly."""
        dark_qr_path = os.path.join("datasets", "qr", "safe", "prmod QR code real.jpeg")
        if os.path.exists(dark_qr_path):
            with open(dark_qr_path, "rb") as f:
                img_bytes = f.read()
            res = analyze_qrcode(img_bytes)
            self.assertEqual(res["status"], "safe")
            self.assertLessEqual(res["risk_score"], 20)
            self.assertEqual(res["classification"], "OTHER_UPI_QR_NOT_REGISTERED")
            self.assertEqual(res["payment_to"], "8105608047@ibl")
            self.assertEqual(res["payee_name"], "JAYAKANTA BHUPAL MUNNOLI")
            self.assertTrue(res["diagnostics"]["is_dark_theme"])

    # --------------------------------------------------------------------------
    # Test 3: Stylized PhonePe QR with Center Logo
    # --------------------------------------------------------------------------
    def test_03_stylized_phonepe_qr_with_center_logo(self):
        """Test 3: Stylized PhonePe QR with dark background and colored center logo decodes properly."""
        stylized_path = os.path.join("datasets", "qr", "safe", "realqryuvaraj.jpeg")
        if os.path.exists(stylized_path):
            with open(stylized_path, "rb") as f:
                img_bytes = f.read()
            res = analyze_qrcode(img_bytes)
            self.assertEqual(res["status"], "safe")
            self.assertLessEqual(res["risk_score"], 20)
            self.assertEqual(res["classification"], "OTHER_UPI_QR_NOT_REGISTERED")
            self.assertEqual(res["payment_to"], "yuvarajbtalawar@okhdfcbank")
            self.assertEqual(res["payee_name"], "yuvaraj b talawar")
            self.assertTrue(res["diagnostics"]["is_dark_theme"])

    # --------------------------------------------------------------------------
    # Test 4: Result A - Official JCER QR Verified
    # --------------------------------------------------------------------------
    def test_04_official_jcer_qr_verified(self):
        """Test 4: Approved college QR matches active registry record with Result A (safe, risk <= 15)."""
        payload = "upi://pay?pa=jcer.examfees@sbi&pn=JCER%20Examination%20Cell&am=1200.00&cu=INR"
        qr_bytes = make_qr_png_bytes(payload, inverted=True)  # Test with dark-theme QR

        # Register and approve in JCER registry
        reg = register_college_qr(
            image_bytes=qr_bytes,
            filename="jcer_exam_dark.png",
            display_name="JCER Semester Exam Counter",
            payment_purpose="Examination Fees",
            department="Examination & Evaluation Cell",
            official_recipient_name="JCER Examination Cell",
            expected_upi_id="jcer.examfees@sbi",
            expected_amount=1200.00,
            description="Semester end examination fee counter",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        # Scan via API endpoint
        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("scan_exam.png", qr_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "VERIFIED_JCER_COLLEGE_QR")
        self.assertTrue(data["is_college_verified"])
        self.assertEqual(data["status"], "safe")
        self.assertLessEqual(data["risk_score"], 15)
        self.assertEqual(data["registered_display_name"], "JCER Semester Exam Counter")
        self.assertEqual(data["payment_purpose"], "Examination Fees")
        self.assertEqual(data["department"], "Examination & Evaluation Cell")
        self.assertIn("Official JCER College QR Verified", data["reasons"][0])
        self.assertIn(MANDATORY_REGISTRY_NOTICE, data["registry_notice"])

    # --------------------------------------------------------------------------
    # Test 5: Result B - Valid External UPI QR (Not Fake!)
    # --------------------------------------------------------------------------
    def test_05_valid_external_upi_qr(self):
        """Test 5: Decoded legitimate external UPI QR is classified as Result B, not labeled fake."""
        payload = "upi://pay?pa=studentcanteen@okaxis&pn=Campus%20Snack%20Corner&cu=INR"
        qr_bytes = make_qr_png_bytes(payload, inverted=False)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("external_canteen.png", qr_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "OTHER_UPI_QR_NOT_REGISTERED")
        self.assertFalse(data["is_college_verified"])
        self.assertEqual(data["status"], "safe")
        self.assertLessEqual(data["risk_score"], 20)
        self.assertEqual(data["payment_to"], "studentcanteen@okaxis")
        self.assertEqual(data["payee_name"], "Campus Snack Corner")

        # Must NOT claim fake or scam
        for reason in data["reasons"]:
            self.assertNotIn("fake", reason.lower())
            self.assertNotIn("fraud", reason.lower())
            self.assertNotIn("scam", reason.lower())

    # --------------------------------------------------------------------------
    # Test 6: Result C - Known College Recipient With Different Details
    # --------------------------------------------------------------------------
    def test_06_known_college_recipient_details_differ(self):
        """Test 6: Matching college UPI ID but altered fee amount triggers Result C (suspicious, risk 65)."""
        reg_payload = "upi://pay?pa=jcer.dark.fees@sbi&pn=JCER%20Finance&am=5000.00&cu=INR"
        reg_bytes = make_qr_png_bytes(reg_payload)

        # Register official fee of 5000.00
        register_college_qr(
            image_bytes=reg_bytes,
            filename="jcer_fees_official.png",
            display_name="JCER Tuition Fee Counter",
            payment_purpose="Tuition Fees",
            department="Finance & Accounts Office",
            official_recipient_name="JCER Finance",
            expected_upi_id="jcer.dark.fees@sbi",
            expected_amount=5000.00,
            description="Official tuition fee payment counter",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )

        # Student scans a tampered QR demanding 7500.00 instead of 5000.00
        tampered_payload = "upi://pay?pa=jcer.dark.fees@sbi&pn=JCER%20Finance&am=7500.00&cu=INR"
        tampered_bytes = make_qr_png_bytes(tampered_payload, inverted=True)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("tampered_fees.png", tampered_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["classification"], "KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER")
        self.assertFalse(data["is_college_verified"])
        self.assertEqual(data["status"], "suspicious")
        self.assertEqual(data["risk_score"], 65)
        self.assertGreaterEqual(len(data["differing_fields"]), 1)
        self.assertEqual(data["differing_fields"][0]["field"], "Amount")

    # --------------------------------------------------------------------------
    # Test 7: Result D - Decoding Failed / Unreadable Image
    # --------------------------------------------------------------------------
    def test_07_decoding_failed_unreadable_image(self):
        """Test 7: Unreadable / corrupted image returns Result D (insufficient_evidence, risk 0, actionable guidance)."""
        # Create an image containing random noise with no QR pattern
        noise_img = np.random.randint(0, 256, (300, 300, 3), dtype=np.uint8)
        _, noise_bytes = cv2.imencode(".png", noise_img)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("noise.png", noise_bytes.tobytes(), "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "insufficient_evidence")
        self.assertEqual(data["risk_score"], 0)
        self.assertIn(data["classification"], ["DECODING_FAILED", "UNABLE_TO_VERIFY"])
        self.assertFalse(data["is_college_verified"])

        # Check for actionable guidance
        reasons_text = " ".join(data["reasons"])
        self.assertIn("Actionable Guidance", reasons_text)
        # Must not accuse the user of uploading a fake QR
        self.assertNotIn("fake", reasons_text.lower())
        self.assertNotIn("scam", reasons_text.lower())

    # --------------------------------------------------------------------------
    # Test 8: Phishing / Malicious Link Detection
    # --------------------------------------------------------------------------
    def test_08_phishing_link_qr_detection(self):
        """Test 8: QR containing an external HTTP phishing URL is blocked with risk >= 85."""
        payload = "https://phishing-jcer-fees-portal.com/login?redirect=steal"
        phish_bytes = make_qr_png_bytes(payload)

        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("phish_qr.png", phish_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertGreaterEqual(data["risk_score"], 85)
        self.assertEqual(data["status"], "blocked")
        self.assertEqual(data["classification"], "SUSPICIOUS_OR_UNSAFE_QR")
        self.assertFalse(data["is_college_verified"])

    # --------------------------------------------------------------------------
    # Test 9: Deactivated Registry Record Not Treated as Active
    # --------------------------------------------------------------------------
    def test_09_deactivated_registry_record(self):
        """Test 9: A deactivated college QR record is not matched as verified."""
        payload = "upi://pay?pa=jcer.deact.fees@sbi&pn=JCER%20Old%20Cell&cu=INR"
        qr_bytes = make_qr_png_bytes(payload)

        reg = register_college_qr(
            image_bytes=qr_bytes,
            filename="deact_qr.png",
            display_name="JCER Deactivated Counter",
            payment_purpose="Other Approved College Payment",
            department="Finance & Accounts Office",
            official_recipient_name="JCER Old Cell",
            expected_upi_id="jcer.deact.fees@sbi",
            admin_user=self.cyberadmin_user,
            auto_approve=True,
        )
        rec_id = reg.get("record_id") or reg["record"]["record_id"]

        # Deactivate
        deactivate_qr(rec_id, self.cyberadmin_user)

        # Scan
        response = client.post(
            "/api/qrcode/analyze",
            files={"file": ("scan_deact.png", qr_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Should NOT be verified
        self.assertNotEqual(data["classification"], "VERIFIED_JCER_COLLEGE_QR")
        self.assertFalse(data["is_college_verified"])

    # --------------------------------------------------------------------------
    # Test 10: Robust Parameter Extraction & URL Unquoting
    # --------------------------------------------------------------------------
    def test_10_parameter_extraction_and_unquoting(self):
        """Test 10: Parameters with URL encoding and special characters are unquoted and normalized."""
        uri = "upi://pay?pa=test.store@okaxis&pn=JCER%20Book%20Store%20%26%20Stationery&am=450.50&cu=INR&tn=Semester%20Books&aid=uGICAgKDUz4jaZg&mode=02&purpose=00"
        parsed = _parse_upi_uri(uri)

        self.assertTrue(parsed["is_upi"])
        self.assertEqual(parsed["pa"], "test.store@okaxis")
        self.assertEqual(parsed["pn"], "JCER Book Store & Stationery")
        self.assertEqual(parsed["am"], "450.50")
        self.assertEqual(parsed["cu"], "INR")
        self.assertEqual(parsed["tn"], "Semester Books")
        self.assertEqual(parsed["aid"], "uGICAgKDUz4jaZg")
        self.assertEqual(parsed["mode"], "02")
        self.assertEqual(parsed["purpose"], "00")

    # --------------------------------------------------------------------------
    # Test 11: CyberAdmin Decode Preview with Dark Theme
    # --------------------------------------------------------------------------
    def test_11_cyberadmin_decode_preview_dark_theme(self):
        """Test 11: CyberAdmin preview endpoint successfully decodes dark-theme QR images."""
        payload = "upi://pay?pa=jcer.hostel@sbi&pn=JCER%20Hostel%20Office&am=25000.00&cu=INR"
        dark_bytes = make_qr_png_bytes(payload, inverted=True)

        response = client.post(
            "/api/cyberadmin/college-qr/decode-preview",
            files={"file": ("dark_preview.png", dark_bytes, "image/png")},
            headers=self.admin_headers,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(data["extracted_fields"]["expected_upi_id"], "jcer.hostel@sbi")
        self.assertEqual(data["extracted_fields"]["official_recipient_name"], "JCER Hostel Office")
        self.assertEqual(data["extracted_fields"]["expected_amount"], 25000.00)
        self.assertTrue(data["diagnostics"]["is_dark_theme"])

    # --------------------------------------------------------------------------
    # Test 12: Polarity Detection and Diagnostics
    # --------------------------------------------------------------------------
    def test_12_polarity_detection_and_diagnostics(self):
        """Test 12: Image background polarity is correctly sensed for light and dark images."""
        light_bytes = make_qr_png_bytes("upi://pay?pa=test1@sbi&pn=Light", inverted=False)
        dark_bytes = make_qr_png_bytes("upi://pay?pa=test2@sbi&pn=Dark", inverted=True)

        nparr_light = np.frombuffer(light_bytes, np.uint8)
        img_light = cv2.imdecode(nparr_light, cv2.IMREAD_COLOR)

        nparr_dark = np.frombuffer(dark_bytes, np.uint8)
        img_dark = cv2.imdecode(nparr_dark, cv2.IMREAD_COLOR)

        is_dark_l, _ = _is_dark_background(img_light)
        is_dark_d, _ = _is_dark_background(img_dark)

        self.assertFalse(is_dark_l)
        self.assertTrue(is_dark_d)


if __name__ == "__main__":
    unittest.main()
