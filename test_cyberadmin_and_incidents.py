# -*- coding: utf-8 -*-
"""
Verification tests for CyberAdmin authorization and Incident Management API
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session

client = TestClient(app)


class TestCyberAdminAndIncidents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. CyberAdmin user
        cyberadmin_data = {
            "id": "CA-001",
            "email": "cyberadmin@jcer.edu.in",
            "name": "Prof. Shivakumar",
            "role": "CYBERADMIN",
            "department": "Campus Information Security",
        }
        cls.cyberadmin_token = generate_signalsafe_session(cyberadmin_data)["token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.cyberadmin_token}"}

        # 2. Student user
        student_data = {
            "id": "STU-001",
            "email": "student.test@jcer.edu.in",
            "name": "Rohan Deshmukh",
            "role": "STUDENT",
            "department": "Computer Science & Engineering",
        }
        cls.student_token = generate_signalsafe_session(student_data)["token"]
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

    def test_01_student_blocked_from_cyberadmin_endpoints(self):
        """Verify student cannot access CyberAdmin stats or incident queue."""
        # Stats
        res_stats = client.get("/api/incidents/stats", headers=self.student_headers)
        self.assertEqual(res_stats.status_code, 403)
        self.assertIn("CyberAdmin authorization required", res_stats.json().get("detail", ""))

        # Incidents list
        res_list = client.get("/api/incidents", headers=self.student_headers)
        self.assertEqual(res_list.status_code, 403)

    def test_02_cyberadmin_can_access_stats_and_queue(self):
        """Verify CyberAdmin can access incident stats and queue."""
        # Stats
        res_stats = client.get("/api/incidents/stats", headers=self.admin_headers)
        self.assertEqual(res_stats.status_code, 200)
        data_stats = res_stats.json()
        self.assertIn("total_incidents", data_stats)
        self.assertIn("pending_reviews", data_stats)
        self.assertIn("resolved_incidents", data_stats)
        self.assertIn("screenshots_analyzed", data_stats)
        self.assertGreaterEqual(data_stats["total_incidents"], 1)

        # Incidents list
        res_list = client.get("/api/incidents", headers=self.admin_headers)
        self.assertEqual(res_list.status_code, 200)
        data_list = res_list.json()
        self.assertIn("incidents", data_list)
        self.assertIn("total", data_list)
        self.assertGreaterEqual(len(data_list["incidents"]), 1)

    def test_03_student_can_submit_incident_report(self):
        """Verify student can submit a security incident report."""
        payload = {
            "category": "phishing_url",
            "target_evidence": "http://malicious-scholarship-portal.test",
            "description": "Fake scholarship application asking for UPI PIN and fee.",
            "severity": "High",
        }
        res = client.post("/api/incidents", json=payload, headers=self.student_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["reported_by"], "Rohan Deshmukh")
        self.assertEqual(data["reporter_role"], "STUDENT")
        self.assertEqual(data["status"], "Pending")

        # CyberAdmin can view this newly submitted report
        new_id = data["id"]
        res_detail = client.get(f"/api/incidents/{new_id}", headers=self.admin_headers)
        self.assertEqual(res_detail.status_code, 200)
        self.assertEqual(res_detail.json()["id"], new_id)

    def test_04_cyberadmin_can_update_status_and_add_notes(self):
        """Verify CyberAdmin can transition incident status and add investigation notes."""
        # First submit an incident
        res = client.post(
            "/api/incidents",
            json={
                "category": "upi_qr_scam",
                "target_evidence": "upi://pay?pa=tampered@bank",
                "description": "Counterfeit QR code spotted in library printer stall.",
                "severity": "Critical",
            },
            headers=self.student_headers,
        )
        self.assertEqual(res.status_code, 201)
        incident_id = res.json()["id"]

        # Student cannot update status
        res_stud_upd = client.patch(
            f"/api/incidents/{incident_id}/status",
            json={"status": "Under Review", "note": "Attempted by student"},
            headers=self.student_headers,
        )
        self.assertEqual(res_stud_upd.status_code, 403)

        # CyberAdmin updates status to Under Review
        res_admin_upd = client.patch(
            f"/api/incidents/{incident_id}/status",
            json={"status": "Under Review", "note": "Dispatching campus security to library."},
            headers=self.admin_headers,
        )
        self.assertEqual(res_admin_upd.status_code, 200)
        data_upd = res_admin_upd.json()
        self.assertEqual(data_upd["status"], "Under Review")
        self.assertGreaterEqual(len(data_upd["audit_trail"]), 2)

        # CyberAdmin adds investigation note
        res_note = client.post(
            f"/api/incidents/{incident_id}/notes",
            json={"note": "CCTV checked, suspect identified, standee secured."},
            headers=self.admin_headers,
        )
        self.assertEqual(res_note.status_code, 200)
        self.assertGreaterEqual(len(res_note.json()["notes"]), 1)

        # CyberAdmin resolves the incident
        res_res = client.patch(
            f"/api/incidents/{incident_id}/status",
            json={"status": "Resolved", "note": "Replaced with tamper-proof QR standee."},
            headers=self.admin_headers,
        )
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json()["status"], "Resolved")

    def test_05_invalid_status_transition_rejected(self):
        """Verify invalid statuses are rejected with 400 Bad Request."""
        res_list = client.get("/api/incidents", headers=self.admin_headers)
        inc_id = res_list.json()["incidents"][0]["id"]

        res_bad = client.patch(
            f"/api/incidents/{inc_id}/status",
            json={"status": "NonExistentStatus"},
            headers=self.admin_headers,
        )
        self.assertEqual(res_bad.status_code, 400)

    def test_06_tampered_token_rejected_and_cannot_escalate(self):
        """Verify a student cannot escalate privileges by tampering with token payload."""
        # A forged token signed with wrong secret or corrupted payload
        fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTYiLCJyb2xlIjoiQ1lCRVJBRE1JTiJ9.fakesignature"
        res_fake = client.get("/api/incidents/stats", headers={"Authorization": f"Bearer {fake_token}"})
        self.assertEqual(res_fake.status_code, 401)

    def test_07_erp_cyberadmin_role_issuance(self):
        """Verify ERP user with role CYBERADMIN generates authoritative CyberAdmin session."""
        erp_user_profile = {
            "id": "ERP-CA-99",
            "email": "security.officer@jcer.edu.in",
            "name": "Dr. Raghavendra",
            "role": "CYBERADMIN",
            "department": {"name": "Campus IT Security", "code": "ITS"},
        }
        session = generate_signalsafe_session(erp_user_profile)
        self.assertEqual(session["user"]["role"], "CYBERADMIN")
        
        # Test accessing cyberadmin endpoint with this token
        ca_headers = {"Authorization": f"Bearer {session['token']}"}
        res_stats = client.get("/api/incidents/stats", headers=ca_headers)
        self.assertEqual(res_stats.status_code, 200)

    def test_08_screenshot_counter_increments(self):
        """Verify screenshot analysis increments persistent counter in stats."""
        res_stats_before = client.get("/api/incidents/stats", headers=self.admin_headers).json()
        before_count = res_stats_before["screenshots_analyzed"]

        # Call /api/screenshot/analyze with a small valid 1x1 test image
        test_image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
            b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        res_scan = client.post(
            "/api/screenshot/analyze",
            files={"file": ("test.png", test_image_bytes, "image/png")},
            headers=self.student_headers,
        )
        self.assertEqual(res_scan.status_code, 200)

        res_stats_after = client.get("/api/incidents/stats", headers=self.admin_headers).json()
        after_count = res_stats_after["screenshots_analyzed"]
        self.assertEqual(after_count, before_count + 1)

    def test_09_react_production_spa_serves_client_routes(self):
        """Verify FastAPI serves the React production SPA at / and falls back properly for client routes."""
        res_root = client.get("/")
        self.assertEqual(res_root.status_code, 200)
        self.assertIn("SignalSafe Campus", res_root.text)
        self.assertIn('<div id="root"></div>', res_root.text)

        # Client route fallback: /incidents
        res_spa = client.get("/incidents")
        self.assertEqual(res_spa.status_code, 200)
        self.assertIn("SignalSafe Campus", res_spa.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
