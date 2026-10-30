import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function CyberAdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [backendHealth, setBackendHealth] = useState('checking');

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch live backend statistics
      const statsData = await api.getIncidentStats();
      setStats(statsData);

      // 2. Fetch recent incidents
      const incidentList = await api.listIncidents({ page: 1, pageSize: 5 });
      setRecentIncidents(incidentList.incidents || []);

      // 3. Health check
      const health = await api.checkHealth();
      setBackendHealth(health?.status === 'ok' ? 'online' : 'degraded');
    } catch (err) {
      console.error('CyberAdmin dashboard fetch error:', err);
      setError(err.message || 'Failed to fetch cybersecurity incident data.');
      setBackendHealth('offline');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const getStatusClass = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'pending': return 'status-pending';
      case 'under review': return 'status-review';
      case 'resolved': return 'status-resolved';
      case 'rejected': return 'status-rejected';
      default: return 'status-neutral';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* 4.1 Header */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{
              fontSize: '26px',
              fontWeight: 800,
              color: '#202124',
              letterSpacing: '-0.02em',
            }}>
              CyberAdmin Dashboard
            </h1>
            <span style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '3px 8px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: '#F3E8FF',
              color: '#7138E8',
              border: '1px solid #DDD6FE',
            }}>
              ROLE: {user?.role || 'CYBERADMIN'}
            </span>
          </div>
          <p style={{
            fontSize: '14px',
            color: '#6B7280',
            marginTop: '4px',
            maxWidth: '720px',
          }}>
            Monitor campus cybersecurity incidents and review suspicious screenshots reported by users.
          </p>
          <div style={{ fontSize: '12.5px', color: '#1647A5', fontWeight: 600, marginTop: '6px' }}>
            Authenticated CyberAdmin: {user?.name || 'Administrator'} • Department: {user?.department || 'Information Security'}
          </div>
        </div>

        {/* Refresh Action */}
        <button
          onClick={fetchDashboardData}
          disabled={isLoading}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <span className={`material-symbols-outlined ${isLoading ? 'spin-icon' : ''}`} style={{ fontSize: '18px' }}>
            refresh
          </span>
          <span>Refresh Data</span>
        </button>
      </div>

      {error && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: '#FEF2F2',
          border: '1px solid #FECACA',
          borderRadius: 'var(--radius-md)',
          color: '#DC2626',
          fontSize: '13.5px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <span className="material-symbols-outlined">error</span>
          <span>{error}</span>
        </div>
      )}

      {/* 4.2 Dashboard Statistics (Matches reference screenshot cards row) */}
      <div className="metrics-row">
        {/* Card 1: Dark card for Pending Queue */}
        <div className="metric-card metric-card-dark">
          <div className="metric-card-header">
            <span className="metric-title">PENDING QUEUE</span>
            <span className="metric-dot" style={{ backgroundColor: '#D97706' }} />
          </div>
          <div className="metric-count">
            {stats ? stats.pending_reviews : '–'}
            <span className="metric-sub">reports</span>
          </div>
        </div>

        {/* Card 2: Under Review */}
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-title">UNDER REVIEW</span>
            <span className="metric-dot" style={{ backgroundColor: '#7138E8' }} />
          </div>
          <div className="metric-count">
            {stats ? stats.under_review : '–'}
            <span className="metric-sub">active</span>
          </div>
        </div>

        {/* Card 3: Resolved */}
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-title">RESOLVED</span>
            <span className="metric-dot" style={{ backgroundColor: '#16A34A' }} />
          </div>
          <div className="metric-count">
            {stats ? stats.resolved_incidents : '–'}
            <span className="metric-sub">closed</span>
          </div>
        </div>

        {/* Card 4: Rejected / Invalid */}
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-title">REJECTED</span>
            <span className="metric-dot" style={{ backgroundColor: '#DC2626' }} />
          </div>
          <div className="metric-count">
            {stats ? stats.rejected_incidents : '–'}
            <span className="metric-sub">invalid</span>
          </div>
        </div>

        {/* Card 5: Total Incidents */}
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-title">TOTAL INCIDENTS</span>
            <span className="metric-dot" style={{ backgroundColor: '#2563EB' }} />
          </div>
          <div className="metric-count">
            {stats ? stats.total_incidents : '–'}
            <span className="metric-sub">logged</span>
          </div>
        </div>

        {/* Card 6: Screenshot Scans */}
        <div className="metric-card">
          <div className="metric-card-header">
            <span className="metric-title">SCREENSHOT SCANS</span>
            <span className="metric-dot" style={{ backgroundColor: '#9333EA' }} />
          </div>
          <div className="metric-count">
            {stats ? stats.screenshots_analyzed : '–'}
            <span className="metric-sub">checks</span>
          </div>
        </div>
      </div>

      {/* 4.3 Main Feature Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Card 1: Incident Reports */}
        <div className="feature-card" onClick={() => navigate('/incidents')}>
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
                backgroundColor: '#F3E8FF',
                border: '1px solid #DDD6FE',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#7138E8',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>
                  assignment
                </span>
              </div>
              <span className="status-pill status-pending">
                {stats ? `${stats.pending_reviews} Pending` : 'Review Queue'}
              </span>
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
              Incident Reports
            </h2>
            <p style={{ fontSize: '13.5px', color: '#6B7280', marginTop: '6px', lineHeight: 1.5 }}>
              Review cybersecurity incidents submitted by students and faculty.
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
              Full workflow & audit log
            </span>
            <button
              className="btn-primary"
              onClick={(e) => { e.stopPropagation(); navigate('/incidents'); }}
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <span>Review Reports</span>
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_forward</span>
            </button>
          </div>
        </div>

        {/* Card 2: Screenshot Detector */}
        <div className="feature-card" onClick={() => navigate('/screenshot')}>
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
                backgroundColor: '#EFF6FF',
                border: '1px solid #BFDBFE',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#1647A5',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>
                  image_search
                </span>
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: 600,
                padding: '3px 8px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: backendHealth === 'online' ? '#F0FDF4' : '#FEF2F2',
                color: backendHealth === 'online' ? '#16A34A' : '#DC2626',
                border: `1px solid ${backendHealth === 'online' ? '#BBF7D0' : '#FECACA'}`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
              }}>
                <span style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: backendHealth === 'online' ? '#16A34A' : '#DC2626',
                }} />
                {backendHealth === 'online' ? 'Engine Active' : 'Engine Unavailable'}
              </span>
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
              Screenshot Detector
            </h2>
            <p style={{ fontSize: '13.5px', color: '#6B7280', marginTop: '6px', lineHeight: 1.5 }}>
              Analyze suspicious screenshots using the existing SignalSafe detection engine.
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
              OCR + Structural ML heuristic
            </span>
            <button
              className="btn-primary"
              onClick={(e) => { e.stopPropagation(); navigate('/screenshot'); }}
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <span>Open Detector</span>
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_forward</span>
            </button>
          </div>
        </div>

        {/* Card 3: College QR Registry */}
        <div className="feature-card" onClick={() => navigate('/admin/college-qr')}>
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
                backgroundColor: '#F3E8FF',
                border: '1px solid #DDD6FE',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#7138E8',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>
                  qr_code_2
                </span>
              </div>
              <span style={{
                fontSize: '11px',
                fontWeight: 600,
                padding: '3px 8px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: '#F0FDF4',
                color: '#16A34A',
                border: '1px solid #BBF7D0',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
              }}>
                <span>JCER Official</span>
              </span>
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
              College QR Registry
            </h2>
            <p style={{ fontSize: '13.5px', color: '#6B7280', marginTop: '6px', lineHeight: 1.5 }}>
              Manage approved JCER payment QR codes, review uploads, and set verified recipient targets.
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
              Official Payment Registry
            </span>
            <button
              className="btn-primary"
              onClick={(e) => { e.stopPropagation(); navigate('/admin/college-qr'); }}
              style={{ padding: '7px 14px', fontSize: '12.5px' }}
            >
              <span>Manage QRs</span>
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_forward</span>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Incident Table Section (Matches ERP table styling) */}
      <div className="erp-table-container">
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#202124' }}>
              Recent Incident Activity
            </h3>
            <p style={{ fontSize: '12px', color: '#6B7280', marginTop: '2px' }}>
              Latest reports received across campus departments.
            </p>
          </div>
          <button
            onClick={() => navigate('/incidents')}
            className="btn-outline"
          >
            <span>View All Queue</span>
            <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>arrow_forward</span>
          </button>
        </div>

        <table className="erp-table">
          <thead>
            <tr>
              <th>REPORT ID</th>
              <th>REPORTER INFO</th>
              <th>CATEGORY</th>
              <th>DESCRIPTION</th>
              <th>DATE REPORTED</th>
              <th>STATUS</th>
              <th style={{ textAlign: 'right' }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {recentIncidents.length === 0 ? (
              <tr>
                <td colSpan="7" className="erp-table-empty">
                  NO RECENT INCIDENTS IN QUEUE
                </td>
              </tr>
            ) : (
              recentIncidents.map((inc) => (
                <tr key={inc.id}>
                  <td style={{ fontWeight: 700, color: '#202124' }}>
                    {inc.id}
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{inc.reported_by}</div>
                    <div style={{ fontSize: '11px', color: '#6B7280' }}>
                      {inc.reporter_role} • {inc.reporter_dept || 'Campus'}
                    </div>
                  </td>
                  <td>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: '#F3F4F6',
                      color: '#374151',
                    }}>
                      {inc.category_label || inc.category}
                    </span>
                  </td>
                  <td style={{ maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {inc.description}
                  </td>
                  <td style={{ fontSize: '12px', color: '#6B7280' }}>
                    {new Date(inc.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <span className={`status-pill ${getStatusClass(inc.status)}`}>
                      {inc.status}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      onClick={() => navigate('/incidents')}
                      className="btn-outline"
                      style={{ padding: '5px 10px', fontSize: '11.5px' }}
                    >
                      Investigate
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
