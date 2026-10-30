import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CyberAdminDashboard from './pages/CyberAdminDashboard';
import IncidentReports from './pages/IncidentReports';
import QrSecurity from './pages/QrSecurity';
import WebsiteChecker from './pages/WebsiteChecker';
import LinkScanner from './pages/LinkScanner';
import EmailDetector from './pages/EmailDetector';
import ReportIncident from './pages/ReportIncident';
import ScreenshotScanner from './pages/ScreenshotScanner';
import CyberAdminDatasetManagement from './pages/CyberAdminDatasetManagement';
import CollegeQrManagement from './pages/CollegeQrManagement';
import Profile from './pages/Profile';
import Settings from './pages/Settings';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Route: ERP Authentication */}
          <Route path="/login" element={<Login />} />

          {/* Protected Routes: SignalSafe Campus Portal */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            
            {/* Core Dashboards */}
            <Route path="dashboard" element={<Dashboard />} />
            <Route
              path="cyberadmin"
              element={
                <ProtectedRoute requiredRole="CYBERADMIN">
                  <CyberAdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* CyberAdmin Incident Review Queue */}
            <Route
              path="incidents"
              element={
                <ProtectedRoute requiredRole="CYBERADMIN">
                  <IncidentReports />
                </ProtectedRoute>
              }
            />
            <Route
              path="incidents/:id"
              element={
                <ProtectedRoute requiredRole="CYBERADMIN">
                  <IncidentReports />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/screenshot-datasets"
              element={
                <ProtectedRoute requiredRole="CYBERADMIN">
                  <CyberAdminDatasetManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/college-qr"
              element={
                <ProtectedRoute requiredRole="CYBERADMIN">
                  <CollegeQrManagement />
                </ProtectedRoute>
              }
            />

            {/* Detection Engines & Security Tools */}
            <Route path="screenshot" element={<ScreenshotScanner />} />
            <Route path="screenshot-detector" element={<Navigate to="/screenshot" replace />} />

            <Route path="website" element={<WebsiteChecker />} />
            <Route path="website-checker" element={<Navigate to="/website" replace />} />

            <Route path="link" element={<LinkScanner />} />
            <Route path="link-scanner" element={<Navigate to="/link" replace />} />

            <Route path="qrcode" element={<QrSecurity />} />
            <Route path="qr-security" element={<Navigate to="/qrcode" replace />} />

            <Route path="report" element={<ReportIncident />} />
            <Route path="email" element={<EmailDetector />} />

            {/* User Profile & Security Settings */}
            <Route path="profile" element={<Profile />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
