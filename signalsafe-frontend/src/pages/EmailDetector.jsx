import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function EmailDetector() {
  const navigate = useNavigate();
  const [sender, setSender] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');

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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>mail</span>
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
                Phishing Email Detection
              </h1>
              <span style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: 'var(--radius-full)',
                backgroundColor: '#F3F4F6',
                color: '#6B7280',
                border: '1px solid #E5E7EB',
              }}>
                Coming Soon
              </span>
            </div>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Identify suspicious emails, student impersonation attempts, and spoofed college communication.
            </p>
          </div>
        </div>
      </div>

      {/* Honest Status Notice Banner (Strict adherence to Part 7) */}
      <div style={{
        padding: '18px 22px',
        backgroundColor: '#F3E8FF',
        border: '1px solid #DDD6FE',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px',
      }}>
        <span className="material-symbols-outlined" style={{ fontSize: '24px', color: '#7138E8', marginTop: '2px' }}>
          construction
        </span>
        <div>
          <h2 style={{ fontSize: '15px', fontWeight: 700, color: '#581C87', margin: 0 }}>
            Phishing Email Detection Engine In Development
          </h2>
          <p style={{ fontSize: '13px', color: '#6B21A8', marginTop: '4px', lineHeight: 1.5 }}>
            This feature is currently scheduled for the next SignalSafe Campus milestone. The campus machine-learning pipeline is actively training on academic phishing datasets. Input fields below are rendered in a disabled preview state to prevent simulated or fabricated evaluations.
          </p>
        </div>
      </div>

      {/* Disabled Form Preview Card */}
      <div className="erp-card">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', opacity: 0.75 }}>
          <div>
            <label style={{
              display: 'block',
              fontSize: '11.5px',
              fontWeight: 700,
              color: '#4B5563',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '6px',
            }}>
              Sender Email Address
            </label>
            <input
              type="text"
              className="erp-input"
              placeholder="e.g. accounts@jcer-fees-portal.net"
              value={sender}
              onChange={(e) => setSender(e.target.value)}
              disabled
              style={{ backgroundColor: '#F9FAFB', cursor: 'not-allowed' }}
            />
          </div>

          <div>
            <label style={{
              display: 'block',
              fontSize: '11.5px',
              fontWeight: 700,
              color: '#4B5563',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '6px',
            }}>
              Email Subject Line
            </label>
            <input
              type="text"
              className="erp-input"
              placeholder="e.g. Urgent: Update your student portal credentials"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled
              style={{ backgroundColor: '#F9FAFB', cursor: 'not-allowed' }}
            />
          </div>

          <div>
            <label style={{
              display: 'block',
              fontSize: '11.5px',
              fontWeight: 700,
              color: '#4B5563',
              textTransform: 'uppercase',
              letterSpacing: '0.04em',
              marginBottom: '6px',
            }}>
              Email Message Content
            </label>
            <textarea
              className="erp-input"
              rows="4"
              placeholder="Paste raw email body text..."
              value={body}
              onChange={(e) => setBody(e.target.value)}
              disabled
              style={{ backgroundColor: '#F9FAFB', cursor: 'not-allowed' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn-primary"
              disabled
              style={{ opacity: 0.5, cursor: 'not-allowed' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>lock</span>
              <span>Analysis Unavailable in Preview</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
