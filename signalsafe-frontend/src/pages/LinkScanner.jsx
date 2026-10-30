import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import RiskScoreMeter from '../components/common/RiskScoreMeter';

export default function LinkScanner() {
  const navigate = useNavigate();
  const [link, setLink] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleScan = async (e) => {
    e.preventDefault();
    if (!link.trim()) return;

    setIsScanning(true);
    setErrorMessage(null);
    try {
      const data = await api.analyzeMaliciousLink(link);
      setResult(data);
    } catch (err) {
      console.error('Link scan error:', err);
      setErrorMessage(err.message || 'Link analysis failed. Please verify the URL structure.');
    } finally {
      setIsScanning(false);
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>link</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              Malicious Link Checker
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Inspect shortened links, redirection chains, and IP hosts received via SMS or messaging apps.
            </p>
          </div>
        </div>
      </div>

      {/* Form Card */}
      <div className="erp-card">
        <form onSubmit={handleScan}>
          <label style={{
            display: 'block',
            fontSize: '11.5px',
            fontWeight: 700,
            color: '#4B5563',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            marginBottom: '8px',
          }}>
            Suspicious Link or Shortened URL
          </label>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '260px' }}>
              <input
                type="text"
                className="erp-input"
                placeholder="e.g. https://bit.ly/3xExamPass or raw IP link"
                value={link}
                onChange={(e) => {
                  setLink(e.target.value);
                  setErrorMessage(null);
                }}
                required
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={isScanning || !link.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              {isScanning ? (
                <>
                  <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>sync</span>
                  <span>Scanning Link...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>troubleshoot</span>
                  <span>Inspect Link</span>
                </>
              )}
            </button>
          </div>
        </form>

        <div style={{
          display: 'flex',
          gap: '8px',
          marginTop: '16px',
          flexWrap: 'wrap',
          fontSize: '12px',
          color: '#6B7280',
          alignItems: 'center',
        }}>
          <span>Quick test:</span>
          <button
            type="button"
            onClick={() => setLink('https://google.com')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#1647A5',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Safe HTTPS Link
          </button>
          <span>•</span>
          <button
            type="button"
            onClick={() => setLink('http://192.168.1.100/login.php')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#7138E8',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Raw IP Address Link
          </button>
        </div>
      </div>

      {/* Error Message */}
      {errorMessage && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#FEF2F2',
          border: '1px solid #FECACA',
          borderRadius: '10px',
          color: '#DC2626',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>error</span>
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Scan Results */}
      {result && <RiskScoreMeter result={result} />}
    </div>
  );
}
