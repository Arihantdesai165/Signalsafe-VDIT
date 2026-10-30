import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import RiskScoreMeter from '../components/common/RiskScoreMeter';

export default function WebsiteChecker() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [reportSuccess, setReportSuccess] = useState(null);

  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsAnalyzing(true);
    setErrorMessage(null);
    setReportSuccess(null);
    try {
      const data = await api.analyzeWebsiteUrl(url);
      setResult(data);
    } catch (err) {
      console.error('URL analysis error:', err);
      setErrorMessage(err.message || 'URL security scan failed. Please check network connection.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReportScam = async () => {
    if (!url.trim()) return;
    try {
      const reportRes = await api.reportScamUrl(url);
      setReportSuccess(`Incident logged successfully! Total community reports: ${reportRes.report_count}`);
      if (result) {
        setResult({ ...result, report_count: reportRes.report_count });
      }
    } catch {
      setErrorMessage('Failed to report URL. Please try again.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>
      {/* Back button and page title */}
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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>travel_explore</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              Fraudulent Website Detection
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Check suspicious domains for phishing patterns, brand impersonation, and fake college portals.
            </p>
          </div>
        </div>
      </div>

      {/* URL Input Form Card */}
      <div className="erp-card">
        <form onSubmit={handleAnalyze}>
          <label style={{
            display: 'block',
            fontSize: '11.5px',
            fontWeight: 700,
            color: '#4B5563',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            marginBottom: '8px',
          }}>
            Suspicious Website Address (URL)
          </label>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '260px' }}>
              <input
                type="text"
                className="erp-input"
                placeholder="e.g. http://paytem-secure-login.xyz/verify"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setErrorMessage(null);
                  setReportSuccess(null);
                }}
                required
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={isAnalyzing || !url.trim()}
              style={{ whiteSpace: 'nowrap' }}
            >
              {isAnalyzing ? (
                <>
                  <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>sync</span>
                  <span>Scanning Website...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>search</span>
                  <span>Check Website</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Informational Guidance Pills */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginTop: '16px',
          flexWrap: 'wrap',
          fontSize: '12px',
          color: '#6B7280',
          alignItems: 'center',
        }}>
          <span>Quick samples:</span>
          <button
            type="button"
            onClick={() => setUrl('http://paytem-secure-login.xyz/verify')}
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
            Sample Phishing Link
          </button>
          <span>•</span>
          <button
            type="button"
            onClick={() => setUrl('https://google.com')}
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
            Sample Legitimate URL
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

      {/* Report Success Feedback */}
      {reportSuccess && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#F0FDF4',
          border: '1px solid #BBF7D0',
          borderRadius: '10px',
          color: '#16A34A',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>check_circle</span>
          <span>{reportSuccess}</span>
        </div>
      )}

      {/* Real Scan Results */}
      {result && (
        <div>
          <RiskScoreMeter result={result} />

          {/* Action Row */}
          <div style={{
            marginTop: '16px',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '12px',
          }}>
            <button
              onClick={handleReportScam}
              className="btn-danger"
              style={{ fontSize: '12.5px', padding: '9px 16px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>flag</span>
              <span>Report URL as Scam</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
