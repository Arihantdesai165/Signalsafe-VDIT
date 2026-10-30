import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>
      {/* Header */}
      <div>
        <button
          onClick={() => navigate('/dashboard')}
          className="btn-secondary"
          style={{ marginBottom: '16px', padding: '7px 12px', fontSize: '12.5px' }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_back</span>
          <span>Back to Dashboard</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            backgroundColor: '#F3E8FF',
            border: '1px solid #DDD6FE',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#7138E8',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>settings</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              System & Security Settings
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Configure active session parameters and review campus security guidelines.
            </p>
          </div>
        </div>
      </div>

      {/* Section 1: Active Session Information */}
      <div className="erp-card">
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#202124', marginBottom: '14px' }}>
          Active Session & Authentication
        </h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 14px',
            backgroundColor: '#F9FAFD',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
          }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#202124' }}>ERP Identity Provider</div>
              <div style={{ fontSize: '11.5px', color: '#6B7280' }}>
                Connected to JCER ERP Authentication Gateway (Belagavi)
              </div>
            </div>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#16A34A', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check_circle</span>
              <span>Authenticated</span>
            </span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 14px',
            backgroundColor: '#F9FAFD',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
          }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#202124' }}>Token Isolation</div>
              <div style={{ fontSize: '11.5px', color: '#6B7280' }}>
                SignalSafe session JWT uses independent signing key (Never stores ERP passwords)
              </div>
            </div>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#7138E8' }}>
              Isolated HS256
            </span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 14px',
            backgroundColor: '#F9FAFD',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
          }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#202124' }}>Cookie Protection</div>
              <div style={{ fontSize: '11.5px', color: '#6B7280' }}>
                HTTP-only, SameSite=Lax session cookie
              </div>
            </div>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#16A34A' }}>
              Secure Storage
            </span>
          </div>
        </div>

        <div style={{ marginTop: '18px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={handleLogout}
            className="btn-danger"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>logout</span>
            <span>Terminate Active Session</span>
          </button>
        </div>
      </div>

      {/* Section 2: Application Preferences */}
      <div className="erp-card">
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#202124', marginBottom: '14px' }}>
          Application Preferences
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 14px',
            backgroundColor: '#FFFFFF',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
          }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#202124' }}>Interface Design System</div>
              <div style={{ fontSize: '11.5px', color: '#6B7280' }}>
                JCER College ERP Light Aesthetic (Lavender & Violet Theme)
              </div>
            </div>
            <span style={{
              fontSize: '11.5px',
              fontWeight: 600,
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: '#F3E8FF',
              color: '#7138E8',
              border: '1px solid #DDD6FE',
            }}>
              System Standard
            </span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 14px',
            backgroundColor: '#F9FAFB',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
          }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#6B7280' }}>Real-time Gateway Telemetry</div>
              <div style={{ fontSize: '11.5px', color: '#9CA3AF' }}>
                Centralized SIEM incident push to Belagavi campus network
              </div>
            </div>
            <span style={{
              fontSize: '11px',
              fontWeight: 600,
              padding: '3px 8px',
              borderRadius: '4px',
              backgroundColor: '#F3F4F6',
              color: '#6B7280',
            }}>
              Coming Soon
            </span>
          </div>
        </div>
      </div>

      {/* Section 3: Campus Cybersecurity Guidance */}
      <div className="erp-card">
        <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#202124', marginBottom: '14px' }}>
          Campus Cybersecurity Protocol
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#7138E8', marginTop: '2px' }}>
              check
            </span>
            <span>
              <strong>Never share your JCER ERP password or OTP:</strong> College IT or faculty will never ask for your password over phone or email.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#7138E8', marginTop: '2px' }}>
              check
            </span>
            <span>
              <strong>Inspect Physical Standees:</strong> Always check that UPI QR codes at canteen or book stalls are printed directly on official stands and not pasted over with a sticker.
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#7138E8', marginTop: '2px' }}>
              check
            </span>
            <span>
              <strong>Prompt Reporting:</strong> Forward suspicious SMS headers, fake exam payment links, or manipulated receipts immediately via the Report Incident tab.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
