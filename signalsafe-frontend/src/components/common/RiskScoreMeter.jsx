import React from 'react';

export default function RiskScoreMeter({ result }) {
  if (!result) return null;

  const score = typeof result.risk_score === 'number' ? result.risk_score : 0;
  const status = (result.status || 'unknown').toLowerCase();
  const cls = (result.classification || '').toUpperCase();

  let statusConfig = {
    label: 'Verified Safe',
    badgeClass: 'badge-safe',
    color: '#15803D',
    icon: 'verified_user',
    bg: '#F0FDF4',
    border: '#BBF7D0',
  };

  if (status === 'insufficient_evidence' || cls === 'DECODING_FAILED' || cls === 'UNABLE_TO_VERIFY') {
    statusConfig = {
      label: 'Decoding Failed / Unreadable',
      badgeClass: 'badge-secondary',
      color: '#4B5563',
      icon: 'search_off',
      bg: '#F9FAFB',
      border: '#E5E7EB',
    };
  } else if (status === 'suspicious' || (score > 35 && score <= 70)) {
    statusConfig = {
      label: 'Suspicious Indicators',
      badgeClass: 'badge-warning',
      color: '#D97706',
      icon: 'warning',
      bg: '#FFFBEB',
      border: '#FDE68A',
    };
  } else if (status === 'danger' || status === 'blocked' || score > 70) {
    statusConfig = {
      label: 'High Risk Detected',
      badgeClass: 'badge-danger',
      color: '#DC2626',
      icon: 'gpp_maybe',
      bg: '#FEF2F2',
      border: '#FECACA',
    };
  }

  return (
    <div style={{
      backgroundColor: '#FFFFFF',
      border: '1px solid #E5EAF1',
      borderRadius: '14px',
      padding: '24px',
      boxShadow: 'var(--shadow-card)',
      marginTop: '24px',
    }}>
      {/* Header with Risk Meter and Badge */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px',
        paddingBottom: '20px',
        borderBottom: '1px solid #E5EAF1',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '50%',
            backgroundColor: statusConfig.bg,
            border: `2px solid ${statusConfig.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: statusConfig.color,
            fontSize: '17px',
            fontWeight: 700,
          }}>
            {score}%
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className={`badge ${statusConfig.badgeClass}`}>
                <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>
                  {statusConfig.icon}
                </span>
                {statusConfig.label}
              </span>
              <span style={{ fontSize: '12px', color: '#8F9CAE' }}>
                Confidence: {result.confidence || 'High'}
              </span>
            </div>
            <p style={{ fontSize: '13.5px', color: '#68778D', marginTop: '4px' }}>
              {result.evidence_summary || 'Security analysis complete.'}
            </p>
          </div>
        </div>

        {/* Risk Level Bar */}
        <div style={{ minWidth: '200px', flex: 1, maxWidth: '280px' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '10px',
            fontWeight: 600,
            color: '#8F9CAE',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            marginBottom: '6px',
          }}>
            <span>Safe (0%)</span>
            <span>Risk Score: {score}/100</span>
            <span>Severe (100%)</span>
          </div>
          <div style={{
            height: '8px',
            backgroundColor: '#F1F5F9',
            borderRadius: '9999px',
            overflow: 'hidden',
          }}>
            <div style={{
              height: '100%',
              width: `${Math.min(100, Math.max(0, score))}%`,
              backgroundColor: statusConfig.color,
              borderRadius: '9999px',
              transition: 'width 0.6s ease-out',
            }} />
          </div>
        </div>
      </div>

      {/* Analysis Evidence & Reasons */}
      {result.reasons && result.reasons.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4 style={{
            fontSize: '12px',
            fontWeight: 600,
            color: '#8F9CAE',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '10px',
          }}>
            Identified Risk Indicators & Findings
          </h4>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {result.reasons.map((reason, idx) => (
              <li
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  fontSize: '13px',
                  color: '#243247',
                  padding: '10px 14px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: '8px',
                  border: '1px solid #E5EAF1',
                }}
              >
                <span className="material-symbols-outlined" style={{
                  fontSize: '16px',
                  color: statusConfig.color,
                  marginTop: '2px',
                  flexShrink: 0,
                }}>
                  {status === 'safe' ? 'check_circle' : 'info'}
                </span>
                <span>{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Extracted Technical Metadata */}
      {result.extracted_fields && Object.keys(result.extracted_fields).length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4 style={{
            fontSize: '12px',
            fontWeight: 600,
            color: '#8F9CAE',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '10px',
          }}>
            Extracted Technical Metadata
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '10px',
          }}>
            {Object.entries(result.extracted_fields).map(([key, val]) => (
              <div
                key={key}
                style={{
                  padding: '10px 14px',
                  backgroundColor: '#F8FAFC',
                  borderRadius: '8px',
                  border: '1px solid #E5EAF1',
                }}
              >
                <span style={{ fontSize: '10.5px', color: '#8F9CAE', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  {key.replace(/_/g, ' ')}
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#243247', marginTop: '2px', display: 'block', wordBreak: 'break-all' }}>
                  {String(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
