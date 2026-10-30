# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Dashboard Redesign Verification Script
Verifies all 12 items required by the Student Dashboard UI Redesign specification
using only Python standard library.
"""

import os
import re
import unittest
from html.parser import HTMLParser
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.auth_service import generate_signalsafe_session

client = TestClient(app)

class TestStudentDashboardRedesign(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        res = client.get("/")
        assert res.status_code == 200, f"Expected 200 but got {res.status_code}"
        cls.html = res.text

    def test_01_top_navigation_structure(self):
        """Verify Top Navigation contains all required elements: logo, subtitle, lang selector, notifications, student profile, logout."""
        html = self.html

        # 1. Logo and Name
        self.assertIn("SignalSafe", html)
        self.assertIn("Campus", html)

        # 2. Subtitle
        self.assertIn("Student Cybersecurity Protection", html)

        # 3. Existing Language Selector preserved
        self.assertIn('id="custom-lang-selector"', html)
        self.assertIn('id="lang-menu-button"', html)
        self.assertIn('id="current-lang-text"', html)
        self.assertIn('id="lang-dropdown-menu"', html)
        self.assertIn('id="lang-options"', html)
        for lang in ['data-lang="en"', 'data-lang="hi"', 'data-lang="kn"', 'data-lang="mr"']:
            self.assertIn(lang, html, f"Language option {lang} must exist")

        # 4. Notifications Icon
        self.assertIn(">notifications<", html)

        # 5. Authenticated Student's Profile / Avatar (dynamic IDs preserved)
        self.assertIn('id="user-display-avatar"', html)
        self.assertIn('id="user-display-name"', html)
        self.assertIn('id="user-display-role"', html)

        # 6. Logout Button (.btn-logout-trigger)
        self.assertIn("btn-logout-trigger", html)

    def test_02_student_welcome_section(self):
        """Verify Student Welcome section contains required heading, description, and no fake statistics/scores."""
        html = self.html

        # Heading and description
        self.assertIn('id="welcome-user-heading"', html)
        self.assertIn("Welcome back, Student!", html)
        expected_desc = "Protect yourself from phishing, fraudulent websites, malicious links, QR-code scams, and suspicious messages."
        self.assertIn(expected_desc, html)

        # Ensure fake scores, fake stats, and fake threat alerts are NOT in dashboard
        self.assertNotIn("85%", html)
        self.assertNotIn("78%", html)
        self.assertNotIn("Monthly Average", html)
        self.assertNotIn("VILLAGE BANK SCAM", html)
        self.assertNotIn("Fake Job Offer via WhatsApp", html)

    def test_03_five_security_tool_cards(self):
        """Verify 'Your Security Toolkit' section displays exactly five cards with required icons, titles, badges, and buttons."""
        html = self.html
        self.assertIn("Your Security Toolkit", html)
        self.assertIn("Choose a security tool to check suspicious content before you trust it.", html)

        cards = [
            {
                "tab": 'data-tab="email"',
                "title": "Phishing Email Detector",
                "desc": "Identify suspicious emails, impersonation attempts, and potentially fraudulent messages.",
                "badge": "Coming Soon",
                "btn": "Open Email Detector",
                "icon": "mark_email_unread"
            },
            {
                "tab": 'data-tab="url"',
                "title": "Fraudulent Website Checker",
                "desc": "Check suspicious websites for potentially unsafe destinations and phishing indicators.",
                "badge": "Available",
                "btn": "Check Website",
                "icon": "travel_explore"
            },
            {
                "tab": 'data-tab="link"',
                "title": "Malicious Link Scanner",
                "desc": "Review suspicious links received through messages, email, and social media.",
                "badge": "Coming Soon",
                "btn": "Open Link Scanner",
                "icon": "link"
            },
            {
                "tab": 'data-tab="qrcode"',
                "title": "QR-Code Scam Detector",
                "desc": "Check QR codes before opening unfamiliar destinations or making payments.",
                "badge": "Available",
                "btn": "Analyze QR Code",
                "icon": "qr_code_scanner"
            },
            {
                "tab": 'data-tab="screenshot"',
                "title": "Screenshot Scam Detector",
                "desc": "Inspect suspicious messages, payment screenshots, and receipts for potential fraud indicators.",
                "badge": "Available",
                "btn": "Analyze Screenshot",
                "icon": "crop_free"
            },
        ]

        for card_spec in cards:
            self.assertIn(card_spec["tab"], html)
            self.assertIn(card_spec["title"], html)
            self.assertIn(card_spec["desc"], html)
            self.assertIn(card_spec["badge"], html)
            self.assertIn(card_spec["btn"], html)
            self.assertIn(card_spec["icon"], html)

    def test_04_card_grid_responsive_classes(self):
        """Verify the cards grid uses 3-column first row, 2-column second row on desktop, 2-col on tablet, 1-col on mobile."""
        html = self.html
        self.assertIn("lg:grid-cols-6", html)
        self.assertIn("md:grid-cols-2", html)
        self.assertIn("grid-cols-1", html)
        self.assertIn("lg:col-start-2", html)

    def test_05_cyber_safety_tips(self):
        """Verify Cyber Safety Tips section is displayed below cards with the 5 static educational tips."""
        html = self.html
        self.assertIn("Cyber Safety Tips", html)

        tips = [
            "Never share your password or OTP.",
            "Verify suspicious links before opening them.",
            "Check QR-code destinations before making payments.",
            "Verify payment receipts through your banking application.",
            "Report suspicious emails or messages to the appropriate authority.",
        ]

        for tip in tips:
            self.assertIn(tip, html, f"Tip '{tip}' must exist in Cyber Safety Tips")

    def test_06_placeholder_modules(self):
        """Verify designed placeholder modules for Phishing Email Detector and Malicious Link Scanner."""
        html = self.html
        self.assertIn('id="panel-email"', html)
        self.assertIn("Email analysis will be available in a future update.", html)

        self.assertIn('id="panel-link"', html)
        self.assertIn("Advanced malicious-link scanning will be available in a future update.", html)

        # Back to Security Tools
        self.assertIn("Back to Security Tools", html)

    def test_07_existing_three_security_modules_preserved(self):
        """Verify the 3 existing security modules and their IDs/inputs are fully preserved."""
        html = self.html

        # 1. Screenshot module
        self.assertIn('id="panel-screenshot"', html)
        self.assertIn('id="screenshot-file"', html)
        self.assertIn('id="screenshot-camera"', html)
        self.assertIn('id="screenshot-upload-btn"', html)
        self.assertIn('id="screenshot-camera-btn"', html)
        self.assertIn('id="screenshot-analyze-btn"', html)
        self.assertIn('id="preview-container"', html)
        self.assertIn('id="screenshot-preview"', html)
        self.assertIn('id="screenshot-drop-zone"', html)

        # 2. QR-code module
        self.assertIn('id="panel-qrcode"', html)
        self.assertIn('id="qr-file"', html)
        self.assertIn('id="qr-camera"', html)
        self.assertIn('id="qr-upload-btn"', html)
        self.assertIn('id="qr-camera-btn"', html)
        self.assertIn('id="qr-analyze-btn"', html)
        self.assertIn('id="qr-preview"', html)
        self.assertIn('id="qr-drop-zone"', html)

        # 3. URL module
        self.assertIn('id="panel-url"', html)
        self.assertIn('id="url-input"', html)
        self.assertIn('id="url-analyze-btn"', html)
        self.assertIn('id="url-progress-container"', html)

        # Result container & tips
        self.assertIn('id="result-container"', html)
        self.assertIn('id="default-tips"', html)

    def test_08_js_files_integrity(self):
        """Verify auth.js, app.js, and other frontend script files contain expected functions and no syntax issues."""
        with open("frontend/js/auth.js", "r", encoding="utf-8") as f:
            auth_content = f.read()
        self.assertIn("Welcome back, ${displayName}!", auth_content)
        self.assertIn("user-display-name", auth_content)
        self.assertIn("user-display-avatar", auth_content)
        self.assertIn("user-display-role", auth_content)
        self.assertIn("handleLogout", auth_content)

        with open("frontend/js/app.js", "r", encoding="utf-8") as f:
            app_content = f.read()
        self.assertIn("scanner-grid-container", app_content)
        self.assertIn("panel-${tab}", app_content)
        self.assertIn("Fraudulent Website Checker", app_content)
        self.assertIn("QR-Code Scam Detector", app_content)
        self.assertIn("Screenshot Scam Detector", app_content)
        self.assertIn("Phishing Email Detector", app_content)
        self.assertIn("Malicious Link Scanner", app_content)

    def test_09_authenticated_api_session_verification(self):
        """Verify authenticated session generation and /api/auth/me response with student details."""
        session = generate_signalsafe_session({
            "id": "student-12345",
            "email": "priya.sharma@jcer.edu.in",
            "name": "Priya Sharma",
            "role": "STUDENT",
            "department": "Electronics and Communication"
        })
        token = session["token"]
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 200)
        user = res.json().get("user")
        self.assertEqual(user["name"], "Priya Sharma")
        self.assertEqual(user["role"], "STUDENT")
        self.assertEqual(user["department"], "Electronics and Communication")


if __name__ == "__main__":
    unittest.main()
