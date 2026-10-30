# -*- coding: utf-8 -*-
"""
SignalSafe Campus - CyberAdmin Sidebar Navigation Verification Suite.

Validates:
1. CyberAdmin role-specific menu configuration does NOT contain 'QR Code Security'.
2. CyberAdmin role-specific menu DOES contain:
   - CyberAdmin Dashboard
   - Incident Reports
   - Dataset Management
   - College QR Registry
   - Screenshot Detector
   - Website Safety Checker
   - Malicious Link Scanner
   - Admin Profile
   - System Settings
3. Student / non-CyberAdmin navigation explicitly preserves 'QR Code Security'.
4. CyberAdmin College QR Registry endpoints remain fully accessible and functional.
5. Student QR Code Security analysis endpoint remains fully accessible and functional.
"""

import os
import re
import unittest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session

client = TestClient(app)


class TestCyberAdminSidebarNavigation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cyberadmin_user = {
            "id": "CYBER-ADMIN-NAV",
            "erp_user_id": "CYBER-ADMIN-NAV",
            "email": "cyberadmin@jcer.edu",
            "name": "Chief Security Officer",
            "role": "CYBERADMIN",
            "department": "Cybersecurity & IT Cell",
        }
        cls.student_user = {
            "id": "STU-NAV-001",
            "erp_user_id": "STU-NAV-001",
            "email": "student@jcer.edu",
            "name": "Student Tester",
            "role": "STUDENT",
            "department": "Computer Science & Engineering",
        }

        cls.admin_token = generate_signalsafe_session(cls.cyberadmin_user)["token"]
        cls.student_token = generate_signalsafe_session(cls.student_user)["token"]

        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}
        cls.student_headers = {"Authorization": f"Bearer {cls.student_token}"}

        # Read Sidebar.jsx source code
        cls.sidebar_path = os.path.join("signalsafe-frontend", "src", "components", "common", "Sidebar.jsx")
        with open(cls.sidebar_path, "r", encoding="utf-8") as f:
            cls.sidebar_content = f.read()

    def test_01_cyberadmin_nav_excludes_qr_security(self):
        """Verify QR Code Security item is absent from cyberAdminNav configuration."""
        # Extract cyberAdminNav block
        match = re.search(r'const cyberAdminNav = \[(.*?)\];\s*const studentNav', self.sidebar_content, re.DOTALL)
        self.assertIsNotNone(match, "cyberAdminNav array must be defined in Sidebar.jsx")
        cyber_admin_block = match.group(1)

        # Must NOT contain QR Code Security
        self.assertNotIn("QR Code Security", cyber_admin_block)
        self.assertNotIn("path: '/qrcode'", cyber_admin_block)

    def test_02_cyberadmin_nav_contains_all_required_menus(self):
        """Verify CyberAdmin sidebar contains all 9 required menu items."""
        match = re.search(r'const cyberAdminNav = \[(.*?)\];\s*const studentNav', self.sidebar_content, re.DOTALL)
        self.assertIsNotNone(match)
        cyber_admin_block = match.group(1)

        required_items = [
            ("CyberAdmin Dashboard", "/dashboard"),
            ("Incident Reports", "/incidents"),
            ("Dataset Management", "/admin/screenshot-datasets"),
            ("College QR Registry", "/admin/college-qr"),
            ("Screenshot Detector", "/screenshot"),
            ("Website Safety Checker", "/website"),
            ("Malicious Link Scanner", "/link"),
            ("Admin Profile", "/profile"),
            ("System Settings", "/settings"),
        ]

        for label, path in required_items:
            self.assertIn(label, cyber_admin_block, f"Missing CyberAdmin menu item: {label}")
            self.assertIn(path, cyber_admin_block, f"Missing CyberAdmin menu path: {path}")

    def test_03_student_nav_preserves_qr_code_security(self):
        """Verify studentNav preserves QR Code Security menu item."""
        match = re.search(r'const studentNav = \[(.*?)\];\s*const activeNav', self.sidebar_content, re.DOTALL)
        self.assertIsNotNone(match, "studentNav array must be defined in Sidebar.jsx")
        student_block = match.group(1)

        self.assertIn("QR Code Security", student_block)
        self.assertIn("path: '/qrcode'", student_block)

    def test_04_college_qr_registry_accessible_by_cyberadmin(self):
        """Verify College QR Registry backend endpoints remain fully accessible and functional for CyberAdmin."""
        res = client.get("/api/cyberadmin/college-qr/stats", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_registered", data)
        self.assertIn("active_approved", data)

    def test_05_student_qr_security_analyzer_endpoint_functional(self):
        """Verify QR detection endpoint remains functional for students."""
        qr_file = os.path.join("datasets", "qr", "safe", "unionrealqr.jpeg")
        with open(qr_file, "rb") as f:
            res = client.post(
                "/api/qrcode/analyze",
                files={"file": ("unionrealqr.jpeg", f, "image/jpeg")},
                headers=self.student_headers,
            )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "safe")
        self.assertEqual(data.get("classification"), "OTHER_UPI_QR_NOT_REGISTERED")

    def test_06_production_spa_serves_updated_bundle(self):
        """Verify FastAPI serves the React production SPA without error."""
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn('<div id="root"></div>', res.text)


if __name__ == "__main__":
    unittest.main()

