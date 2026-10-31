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
      </div>
    </div>
  );
}
