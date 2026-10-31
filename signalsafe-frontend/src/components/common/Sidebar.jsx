import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth();
  const isCyberAdmin = (user?.role || '').toUpperCase() === 'CYBERADMIN';

  const cyberAdminNav = [
    {
      section: 'DASHBOARD',
      items: [
        { path: '/dashboard', label: 'CyberAdmin Dashboard', icon: 'dashboard' },
      ],
    },
    {
      section: 'INCIDENT REVIEWS',
      items: [
        { path: '/incidents', label: 'Incident Reports', icon: 'assignment' },
        { path: '/admin/screenshot-datasets', label: 'Dataset Management', icon: 'dataset' },
        { path: '/admin/college-qr', label: 'College QR Registry', icon: 'qr_code_2' },
      ],
    },
    {
      section: 'DETECTION ENGINES',
      items: [
        { path: '/screenshot', label: 'Screenshot Detector', icon: 'image_search' },
        { path: '/website', label: 'Website Safety Checker', icon: 'travel_explore' },
        { path: '/link', label: 'Malicious Link Scanner', icon: 'link' },
      ],
    },
    {
      section: 'ADMINISTRATION',
      items: [
        { path: '/profile', label: 'Admin Profile', icon: 'person' },
        { path: '/settings', label: 'System Settings', icon: 'settings' },
      ],
    },
  ];

  const studentNav = [
    {
      section: 'DASHBOARD',
      items: [
        { path: '/dashboard', label: 'Student Dashboard', icon: 'dashboard' },
      ],
    },
    {
      section: 'SECURITY TOOLS',
      items: [
        { path: '/website', label: 'Website Safety Checker', icon: 'travel_explore' },
        { path: '/link', label: 'Malicious Link Scanner', icon: 'link' },
        { path: '/qrcode', label: 'QR Code Security', icon: 'qr_code_scanner' },
        { path: '/report', label: 'Report Incident', icon: 'flag' },
        { path: '/email', label: 'Phishing Email', icon: 'mail', badge: 'Preview' },
      ],
    },
    {
      section: 'ACCOUNT',
      items: [
        { path: '/profile', label: 'My Profile', icon: 'person' },
        { path: '/settings', label: 'Security Settings', icon: 'settings' },
      ],
    },
  ];

  const activeNav = isCyberAdmin ? cyberAdminNav : studentNav;

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(32, 33, 36, 0.4)',
            backdropFilter: 'blur(2px)',
            zIndex: 45,
          }}
          className="mobile-sidebar-backdrop"
        />
      )}

      <aside className={`app-sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Top ERP Branding Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {/* JGI Seal Mark */}
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              backgroundColor: '#1E3A8A',
              background: 'linear-gradient(135deg, #1E3A8A 0%, #172554 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
              fontWeight: 800,
              fontSize: '13px',
              letterSpacing: '0.05em',
              boxShadow: '0 2px 6px rgba(30, 58, 138, 0.3)',
              border: '2px solid #DBEAFE',
            }}>
              JGI
            </div>
            <div>
              <div style={{
                fontSize: '15px',
                fontWeight: 800,
                color: '#202124',
                letterSpacing: '-0.02em',
                lineHeight: 1.1,
              }}>
                JCER ERP
              </div>
              <div style={{
                fontSize: '11px',
                fontWeight: 600,
                color: '#6B7280',
                marginTop: '2px',
              }}>
                {isCyberAdmin ? 'CyberAdmin Portal' : 'SignalSafe Campus'}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="mobile-close-btn"
            style={{
              display: 'none',
              background: 'none',
              border: 'none',
              color: '#6B7280',
              cursor: 'pointer',
              padding: '4px',
            }}
            aria-label="Close Navigation"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>close</span>
          </button>
        </div>

        {/* Navigation Sections */}
        <nav style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
          {activeNav.map((sec, secIdx) => (
            <div key={secIdx}>
              <div className="nav-section-title">{sec.section}</div>
              {sec.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onClose}
                  className={({ isActive }) => `nav-item-link ${isActive ? 'active' : ''}`}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: 1 }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '20px', flexShrink: 0 }}>{item.icon}</span>
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span style={{
                      fontSize: '10.5px',
                      fontWeight: 700,
                      padding: '2px 7px',
                      borderRadius: '4px',
                      backgroundColor: '#F3E8FF',
                      color: '#7138E8',
                      flexShrink: 0,
                    }}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Bottom Role & Academic Year Card (From reference screenshot) */}
        <div className="sidebar-bottom-info">
          <div className="sidebar-status-box">
            <div className="sidebar-info-row">
              <span className="sidebar-info-label">Role</span>
              <span className="sidebar-info-val">
                {isCyberAdmin ? 'CYBERADMIN' : (user?.role || 'STUDENT')}
              </span>
            </div>
            <div className="sidebar-info-row">
              <span className="sidebar-info-label">Academic Year</span>
              <span className="sidebar-info-val">2026–27</span>
            </div>
            <div style={{
              marginTop: '10px',
              paddingTop: '8px',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11px',
              color: '#16A34A',
              fontWeight: 600,
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>
                verified_user
              </span>
              <span>Campus Security Active</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
