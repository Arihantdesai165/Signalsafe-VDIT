import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Profile() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const isCyberAdmin = (user?.role || '').toUpperCase() === 'CYBERADMIN';

  const getInitials = (name) => {
    if (!name) return 'CA';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return parts[0].slice(0, 2).toUpperCase();
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>badge</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              Campus Identity Profile
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Authoritative identity information verified from the JCER ERP directory.
            </p>
          </div>
        </div>
      </div>

      {/* Main Profile Card */}
      <div className="erp-card">
        {/* Profile Header Avatar Banner */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '20px',
          paddingBottom: '24px',
          borderBottom: '1px solid var(--border-color)',
        }}>
          <div style={{
            width: '72px',
            height: '72px',
            borderRadius: '50%',
            backgroundColor: isCyberAdmin ? '#7138E8' : '#1647A5',
            color: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            fontWeight: 800,
            boxShadow: '0 4px 12px rgba(113, 56, 232, 0.25)',
          }}>
            {getInitials(user?.name)}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#202124' }}>
                {user?.name || 'Verified User'}
              </h2>
              <span className={`status-pill ${isCyberAdmin ? 'status-review' : 'status-neutral'}`}>
                {user?.role || 'STUDENT'}
              </span>
            </div>
            <div style={{ fontSize: '13.5px', color: '#6B7280', marginTop: '2px' }}>
              {user?.email || 'N/A'}
            </div>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '11.5px',
              color: '#16A34A',
              fontWeight: 600,
              marginTop: '6px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>verified</span>
              <span>JCER ERP Identity Verified</span>
            </div>
          </div>
        </div>

        {/* Identity Details Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: '16px',
          marginTop: '24px',
        }}>
          <div style={{
            padding: '14px 16px',
            backgroundColor: '#F9FAFD',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Full Display Name
            </span>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#202124', marginTop: '3px' }}>
              {user?.name || '–'}
            </div>
          </div>

          <div style={{
            padding: '14px 16px',
            backgroundColor: '#F9FAFD',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Registered Email / Identifier
            </span>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#202124', marginTop: '3px' }}>
              {user?.email || '–'}
            </div>
          </div>

          <div style={{
            padding: '14px 16px',
            backgroundColor: '#F9FAFD',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Authorized ERP Role
            </span>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#7138E8', marginTop: '3px' }}>
              {user?.role || 'STUDENT'}
            </div>
          </div>

          <div style={{
            padding: '14px 16px',
            backgroundColor: '#F9FAFD',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Campus Department
            </span>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#202124', marginTop: '3px' }}>
              {user?.department || (isCyberAdmin ? 'Information Security Office' : 'Computer Science & Engineering')}
            </div>
          </div>

          <div style={{
            padding: '14px 16px',
            backgroundColor: '#F9FAFD',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Authentication Source
            </span>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#1647A5', marginTop: '3px' }}>
              JCER ERP Identity Gateway
            </div>
          </div>

          <div style={{
            padding: '14px 16px',
            backgroundColor: '#F9FAFD',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-md)',
          }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Session Status
            </span>
            <div style={{ fontSize: '14px', fontWeight: 700, color: '#16A34A', marginTop: '3px' }}>
              Active (24-Hour Isolated JWT)
            </div>
          </div>
        </div>

        {/* Source of Truth Disclaimer */}
        <div style={{
          marginTop: '24px',
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: '#FFFBEB',
          border: '1px solid #FDE68A',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          fontSize: '12.5px',
          color: '#92400E',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#D97706', marginTop: '1px' }}>
            info
          </span>
          <div>
            <strong>Source of Truth:</strong> Your user identity and role are managed authoritatively by the JCER ERP System. Role promotions and password resets must be initiated through the central ERP portal.
          </div>
        </div>
      </div>
    </div>
  );
}
