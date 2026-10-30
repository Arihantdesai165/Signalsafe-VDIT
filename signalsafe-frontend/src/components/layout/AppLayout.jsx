import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../common/Sidebar';
import TopNav from '../common/TopNav';

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Viewport Content Area */}
      <div className="main-viewport">
        {/* Top Navigation Bar with Profile & Notifications */}
        <TopNav onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

        {/* Dynamic Route Content */}
        <main className="page-content">
          <Outlet />
        </main>

        {/* ERP Footer (Exact layout from reference screenshot) */}
        <footer className="app-footer">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', marginBottom: '8px' }}>
            <a href="#terms" onClick={(e) => e.preventDefault()}>Terms & Conditions</a>
            <span style={{ color: '#D1D5DB' }}>•</span>
            <a href="#privacy" onClick={(e) => e.preventDefault()}>Privacy Policy</a>
            <span style={{ color: '#D1D5DB' }}>•</span>
            <a href="#support" onClick={(e) => e.preventDefault()}>Support Desk</a>
          </div>
          <div style={{ color: '#6B7280', marginBottom: '4px' }}>
            © 2026 Jain College of Engineering & Research, Belagavi. All rights reserved.
          </div>
          <div style={{ color: '#9CA3AF', fontSize: '11px', fontWeight: 600 }}>
            Designed & Developed by <span style={{ color: '#1647A5' }}>VYON LABS</span> & SignalSafe Campus
          </div>
        </footer>
      </div>
    </div>
  );
}
