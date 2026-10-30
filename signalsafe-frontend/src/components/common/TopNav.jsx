import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function TopNav({ onToggleSidebar }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const profileRef = useRef(null);
  const notifRef = useRef(null);

  // Close popups on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setShowProfileMenu(false);
      }
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const getInitials = (name) => {
    if (!name) return 'CA';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  };

  const isCyberAdmin = (user?.role || '').toUpperCase() === 'CYBERADMIN';

  // Compute page title from path
  const getPageTitle = () => {
    const path = location.pathname;
    if (path.includes('incidents')) return 'Incident Reports';
    if (path.includes('screenshot')) return 'Screenshot Detector';
    if (path.includes('website')) return 'Website Safety Checker';
    if (path.includes('link')) return 'Malicious Link Scanner';
    if (path.includes('qrcode')) return 'QR Code Security';
    if (path.includes('report')) return 'Report a Security Incident';
    if (path.includes('email')) return 'Phishing Email Detection';
    if (path.includes('profile')) return 'User Profile';
    if (path.includes('settings')) return 'System Settings';
    return isCyberAdmin ? 'CyberAdmin Dashboard' : 'Student Security Dashboard';
  };

  return (
    <header style={{
      position: 'sticky',
      top: 0,
      zIndex: 40,
      backgroundColor: '#FFFFFF',
      borderBottom: '1px solid var(--border-color)',
      padding: '12px 28px',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        maxWidth: '1360px',
        margin: '0 auto',
      }}>
        {/* Left: Mobile Toggle & Page Title */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            onClick={onToggleSidebar}
            style={{
              display: 'none',
              background: '#FFFFFF',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: '#374151',
              cursor: 'pointer',
              padding: '6px',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            className="mobile-sidebar-toggle"
            aria-label="Toggle Sidebar"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>menu</span>
          </button>

          <div>
            <div style={{
              fontSize: '18px',
              fontWeight: 800,
              color: '#202124',
              letterSpacing: '-0.02em',
            }}>
              {getPageTitle()}
            </div>
            <div style={{
              fontSize: '11.5px',
              color: '#6B7280',
              fontWeight: 500,
            }}>
              Jain College of Engineering & Research • Belagavi
            </div>
          </div>
        </div>

        {/* Right: Academic Year, Search, Notifications, Profile Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Academic Year Pill (Matches reference screenshot) */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: '#FFFFFF',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-full)',
            padding: '6px 12px',
            fontSize: '12px',
            fontWeight: 600,
            color: '#374151',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '15px', color: '#6B7280' }}>
              calendar_today
            </span>
            <span>AY: 2026–27</span>
          </div>

          {/* Notification Bell */}
          <div style={{ position: 'relative' }} ref={notifRef}>
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: '#F3F4F6',
                border: '1px solid var(--border-color)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#374151',
                cursor: 'pointer',
                position: 'relative',
              }}
              aria-label="Notifications"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>notifications</span>
              <span style={{
                position: 'absolute',
                top: '7px',
                right: '7px',
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: '#DC2626',
              }} />
            </button>

            {/* Notification Dropdown */}
            {showNotifications && (
              <div style={{
                position: 'absolute',
                right: 0,
                top: '44px',
                width: '320px',
                backgroundColor: '#FFFFFF',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-dropdown)',
                padding: '16px',
                zIndex: 50,
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingBottom: '10px',
                  borderBottom: '1px solid var(--border-color)',
                  marginBottom: '12px',
                }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#202124' }}>Campus Security Advisories</div>
                  <span style={{ fontSize: '11px', color: '#7138E8', fontWeight: 600 }}>Active</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{
                    padding: '8px 10px',
                    borderRadius: '8px',
                    backgroundColor: '#FFFBEB',
                    border: '1px solid #FDE68A',
                    fontSize: '12px',
                  }}>
                    <div style={{ fontWeight: 600, color: '#92400E' }}>Exam Fee Phishing Alert</div>
                    <div style={{ color: '#78350F', fontSize: '11px', marginTop: '2px' }}>
                      Beware of fake SMS links claiming exam registration fee payment via unknown portals.
                    </div>
                  </div>
                  <div style={{
                    padding: '8px 10px',
                    borderRadius: '8px',
                    backgroundColor: '#F3E8FF',
                    border: '1px solid #DDD6FE',
                    fontSize: '12px',
                  }}>
                    <div style={{ fontWeight: 600, color: '#6B21A8' }}>Cafeteria Standee Verification</div>
                    <div style={{ color: '#581C87', fontSize: '11px', marginTop: '2px' }}>
                      Physical QR standees inspected and certified tamper-free by CyberAdmin.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* User Profile Pill (Matches reference screenshot) */}
          <div style={{ position: 'relative' }} ref={profileRef}>
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: '#18181B',
                color: '#FFFFFF',
                borderRadius: 'var(--radius-full)',
                padding: '4px 14px 4px 5px',
                border: 'none',
                cursor: 'pointer',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              }}
            >
              {/* Avatar circle */}
              <div style={{
                width: '28px',
                height: '28px',
                borderRadius: '50%',
                backgroundColor: '#7138E8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '12px',
                fontWeight: 700,
                color: '#FFFFFF',
              }}>
                {getInitials(user?.name)}
              </div>
              <span style={{ fontSize: '12.5px', fontWeight: 600 }}>
                {user?.name || (isCyberAdmin ? 'CyberAdmin' : 'Student')}
              </span>
              <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#A1A1AA' }}>
                keyboard_arrow_down
              </span>
            </button>

            {/* Profile Dropdown */}
            {showProfileMenu && (
              <div style={{
                position: 'absolute',
                right: 0,
                top: '44px',
                width: '240px',
                backgroundColor: '#FFFFFF',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-dropdown)',
                padding: '8px 0',
                zIndex: 50,
              }}>
                <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#202124' }}>
                    {user?.name || 'Authorized User'}
                  </div>
                  <div style={{ fontSize: '11.5px', color: '#6B7280', marginTop: '1px' }}>
                    {user?.email || ''}
                  </div>
                  <div style={{
                    marginTop: '6px',
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: isCyberAdmin ? '#F3E8FF' : '#EFF6FF',
                    color: isCyberAdmin ? '#7138E8' : '#2563EB',
                    fontSize: '10.5px',
                    fontWeight: 700,
                  }}>
                    {isCyberAdmin ? 'CYBERADMIN' : (user?.role || 'STUDENT')}
                  </div>
                </div>

                <div style={{ padding: '4px 0' }}>
                  <button
                    onClick={() => { setShowProfileMenu(false); navigate('/profile'); }}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 16px',
                      background: 'none',
                      border: 'none',
                      textAlign: 'left',
                      fontSize: '13px',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F9FAFB'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#6B7280' }}>
                      person
                    </span>
                    <span>My Profile</span>
                  </button>

                  <button
                    onClick={() => { setShowProfileMenu(false); navigate('/settings'); }}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 16px',
                      background: 'none',
                      border: 'none',
                      textAlign: 'left',
                      fontSize: '13px',
                      color: '#374151',
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F9FAFB'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#6B7280' }}>
                      settings
                    </span>
                    <span>Security Settings</span>
                  </button>
                </div>

                <div style={{ borderTop: '1px solid var(--border-color)', padding: '4px 0 0' }}>
                  <button
                    onClick={handleLogout}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      padding: '8px 16px',
                      background: 'none',
                      border: 'none',
                      textAlign: 'left',
                      fontSize: '13px',
                      color: '#DC2626',
                      fontWeight: 500,
                      cursor: 'pointer',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#FEF2F2'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#DC2626' }}>
                      logout
                    </span>
                    <span>Sign Out Securely</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
