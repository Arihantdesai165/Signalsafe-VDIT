import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import CyberAdminDashboard from './CyberAdminDashboard';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    async function checkBackend() {
      try {
        const res = await api.checkHealth();
        if (res && res.status === 'ok') {
          setBackendStatus('online');
        } else {
          setBackendStatus('degraded');
        }
      } catch {
        setBackendStatus('offline');
      }
    }
    checkBackend();
  }, []);

  // If authenticated user is CYBERADMIN, render the dedicated CyberAdmin Dashboard!
  if ((user?.role || '').toUpperCase() === 'CYBERADMIN') {
    return <CyberAdminDashboard />;
  }

  const featureCards = [
    {
      id: 'website',
      path: '/website',
      title: 'Website Safety Checker',
      description: 'Check suspicious websites and portals for potential phishing indicators and unsafe destinations.',
      icon: 'travel_explore',
      badge: 'Operational',
      buttonText: 'Check Website',
    },
    {
      id: 'link',
      path: '/link',
      title: 'Malicious Link Scanner',
      description: 'Inspect suspicious URLs and links received via SMS, WhatsApp, or email before clicking.',
      icon: 'link',
      badge: 'Operational',
      buttonText: 'Scan Link',
    },
    {
      id: 'qrcode',
      path: '/qrcode',
      title: 'QR Code Security',
      description: 'Decode and inspect UPI QR codes to verify destination accounts before making payments.',
      icon: 'qr_code_scanner',
      badge: 'Operational',
      buttonText: 'Check QR Code',
    },
    {
      id: 'screenshot',
      path: '/screenshot',
      title: 'Screenshot Scam Detector',
      description: 'Analyze UPI payment confirmation screenshots for forged timestamps, fonts, and fake receipts.',
      icon: 'image_search',
      badge: 'Operational',
      buttonText: 'Scan Screenshot',
    },
    {
      id: 'report',
      path: '/report',
      title: 'Report a Security Incident',
      description: 'Report suspected phishing links, fake fee portals, or QR-code tampering to campus CyberAdmin.',
      icon: 'flag',
      badge: 'Direct Queue',
      buttonText: 'Report Incident',
    },
    {
      id: 'email',
      path: '/email',
      title: 'Phishing Email Detection',
      description: 'Analyze suspicious emails and student communication for impersonation and spoofing.',
      icon: 'mail',
      badge: 'Coming Soon',
      buttonText: 'Open Preview',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 1. Student Welcome Section */}
      <div className="erp-card" style={{ padding: '24px 28px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
                Welcome, {user?.name || 'Student'}!
              </h1>
              <span style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '3px 8px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: '#EFF6FF',
                color: '#1647A5',
                border: '1px solid #BFDBFE',
              }}>
                ROLE: {user?.role || 'STUDENT'}
              </span>
            </div>
            <p style={{ fontSize: '13.5px', color: '#6B7280', marginTop: '6px', maxWidth: '680px', lineHeight: 1.5 }}>
              Campus Cybersecurity Portal integrated with JCER ERP. Verify suspicious links, QR codes, and payment receipts.
            </p>
          </div>

          {/* Real Backend Status Indicator */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#F9FAFB',
            padding: '8px 14px',
            borderRadius: 'var(--radius-full)',
            border: '1px solid var(--border-color)',
          }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: backendStatus === 'online' ? '#16A34A' : backendStatus === 'degraded' ? '#D97706' : '#DC2626',
            }} />
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#374151' }}>
              {backendStatus === 'online' ? 'Security Services Active' : backendStatus === 'degraded' ? 'Services Degraded' : 'Backend Connecting'}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Security Toolkit Grid (Light ERP Cards) */}
      <div>
        <div style={{ marginBottom: '14px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 800, color: '#202124', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Campus Cybersecurity Tools
          </h2>
          <p style={{ fontSize: '12.5px', color: '#6B7280' }}>
            Select an operational verification tool to scan suspicious media or content.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
        }}>
          {featureCards.map((feat) => (
            <div
              key={feat.id}
              className="feature-card"
              onClick={() => navigate(feat.path)}
            >
              <div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: '16px',
                }}>
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    backgroundColor: feat.id === 'email' ? '#F3F4F6' : '#F3E8FF',
                    border: `1px solid ${feat.id === 'email' ? '#E5E7EB' : '#DDD6FE'}`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: feat.id === 'email' ? '#6B7280' : '#7138E8',
                  }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>
                      {feat.icon}
                    </span>
                  </div>

                  <span style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-full)',
                    backgroundColor: feat.badge === 'Coming Soon' ? '#F3F4F6' : '#F0FDF4',
                    color: feat.badge === 'Coming Soon' ? '#6B7280' : '#16A34A',
                    border: `1px solid ${feat.badge === 'Coming Soon' ? '#E5E7EB' : '#BBF7D0'}`,
                  }}>
                    {feat.badge}
                  </span>
                </div>

                <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#202124' }}>
                  {feat.title}
                </h3>
                <p style={{ fontSize: '13px', color: '#6B7280', marginTop: '6px', lineHeight: 1.5 }}>
                  {feat.description}
                </p>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '16px',
                borderTop: '1px solid var(--border-color)',
                marginTop: '16px',
              }}>
                <span style={{ fontSize: '12px', color: '#6B7280', fontWeight: 500 }}>
                  Ready to scan
                </span>
                <button
                  className={feat.badge === 'Coming Soon' ? 'btn-secondary' : 'btn-primary'}
                  onClick={(e) => { e.stopPropagation(); navigate(feat.path); }}
                  style={{ padding: '7px 14px', fontSize: '12.5px' }}
                >
                  <span>{feat.buttonText}</span>
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_forward</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
