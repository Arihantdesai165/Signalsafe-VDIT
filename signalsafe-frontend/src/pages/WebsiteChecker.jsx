import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function WebsiteChecker() {
  const navigate = useNavigate();
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [reportSuccess, setReportSuccess] = useState(null);

  const validateInput = (value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      return 'Please enter a website address to check.';
    }
    if (trimmed.length > 2048) {
      return 'URL exceeds the maximum allowed length of 2048 characters.';
    }
    return null;
  };

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    const valError = validateInput(url);
    if (valError) {
      setErrorMessage(valError);
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage(null);
    setReportSuccess(null);
    setResult(null);

    try {
      const data = await api.predictUrlSafety(url, 'website');
      setResult(data);
    } catch (err) {
      console.error('Website safety check error:', err);
      setErrorMessage(err.message || 'Website security scan failed. Please check your connection and retry.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClear = () => {
    setUrl('');
    setResult(null);
    setErrorMessage(null);
    setReportSuccess(null);
  };

  const handleQuickSample = (sampleUrl) => {
    setUrl(sampleUrl);
    setResult(null);
    setErrorMessage(null);
    setReportSuccess(null);
  };

  const handleReportScam = async () => {
    if (!url.trim()) return;
    try {
      const reportRes = await api.reportScamUrl(url);
      setReportSuccess(`Incident logged successfully! Total community reports: ${reportRes.report_count || 1}`);
      if (result) {
        setResult({ ...result, report_count: reportRes.report_count });
      }
    } catch {
      setErrorMessage('Failed to report website to the security queue. Please try again.');
    }
  };

  const isMalicious = result && (result.prediction === 1 || result.classification === 'Malicious');

  return (
<div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>
      {/* Top Header & Navigation */}
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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>travel_explore</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              Website Safety Checker
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Check suspicious websites and portals for potential phishing indicators and unsafe destinations.
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
            Website URL to Check
          </label>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '260px' }}>
              <input
                type="text"
                className="erp-input"
                placeholder="e.g. https://campus-portal-verification.xyz/login or google.com"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);
                  setErrorMessage(null);
                  setReportSuccess(null);
                }}
                disabled={isAnalyzing}
                required
              />
            </div>
            <button
              type="submit"
              className="btn-primary"
              disabled={isAnalyzing || !url.trim()}
              style={{ whiteSpace: 'nowrap', padding: '0 20px' }}
            >
              {isAnalyzing ? (
                <>
                  <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>sync</span>
                  <span>Checking Website...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>search</span>
                  <span>Check Website</span>
                </>
              )}
            </button>
            {url && (
              <button
                type="button"
                className="btn-secondary"
                onClick={handleClear}
                disabled={isAnalyzing}
                style={{ padding: '0 14px' }}
                title="Clear input"
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {/* Quick Sample Test Buttons */}
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
            onClick={() => handleQuickSample('https://www.wikipedia.org')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#16A34A',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Legitimate Website
          </button>
          <span>•</span>
          <button
            type="button"
            onClick={() => handleQuickSample('https://secure-login-verify-account.xyz/login')}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#DC2626',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Malicious Phishing Website
          </button>
          <span>•</span>
          <button
            type="button"
            onClick={() => handleQuickSample('http://192.168.1.10/login')}
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
            IP Host Address
          </button>
        </div>
      </div>

      {/* Error Banner with Retry */}
      {errorMessage && (
        <div style={{
          padding: '14px 18px',
          backgroundColor: '#FEF2F2',
          border: '1px solid #FECACA',
          borderRadius: '12px',
          color: '#DC2626',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>error</span>
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => handleAnalyze()}
            className="btn-secondary"
            style={{ padding: '4px 12px', fontSize: '12px', color: '#DC2626', borderColor: '#FECACA' }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Report Success Toast */}
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

      {/* ML Prediction Result Display */}
      {result && (
        <div style={{
          backgroundColor: '#FFFFFF',
          border: `1px solid ${isMalicious ? '#FECACA' : '#BBF7D0'}`,
          borderRadius: '14px',
          padding: '24px',
          boxShadow: 'var(--shadow-card)',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
        }}>
          {/* Header Status & Confidence Banner */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '14px',
            paddingBottom: '18px',
            borderBottom: `1px solid ${isMalicious ? '#FEE2E2' : '#DCFCE7'}`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: isMalicious ? '#FEF2F2' : '#F0FDF4',
                border: `2px solid ${isMalicious ? '#F87171' : '#4ADE80'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: isMalicious ? '#DC2626' : '#16A34A',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '28px' }}>
                  {isMalicious ? 'dangerous' : 'verified_user'}
                </span>
              </div>
              <div>
                <span style={{
                  display: 'inline-block',
                  fontSize: '12px',
                  fontWeight: 800,
                  letterSpacing: '0.04em',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  backgroundColor: isMalicious ? '#FEF2F2' : '#F0FDF4',
                  color: isMalicious ? '#DC2626' : '#16A34A',
                  border: `1px solid ${isMalicious ? '#FCA5A5' : '#86EFAC'}`,
                  textTransform: 'uppercase',
                }}>
                  {result.status_label || (isMalicious ? 'MALICIOUS WEBSITE' : 'NO MALICIOUS INDICATORS DETECTED')}
                </span>
                <div style={{ fontSize: '13px', color: '#6B7280', marginTop: '4px' }}>
                  {isMalicious ? 'Security Warning: Dangerous Website Destination' : 'Security Assessment: Clean Structure'}
                </div>
              </div>
            </div>

            {/* Model Confidence Badge */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
            }}>
              <span style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280', textTransform: 'uppercase' }}>
                Model Confidence Score
              </span>
              <span style={{
                fontSize: '20px',
                fontWeight: 800,
                color: isMalicious ? '#DC2626' : '#16A34A',
              }}>
                {result.confidence_percentage}%
              </span>
            </div>
          </div>

          {/* Detected Scanned URL Box */}
          <div>
            <span style={{ fontSize: '11.5px', fontWeight: 700, color: '#4B5563', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Checked Website Destination
            </span>
            <div style={{
              marginTop: '6px',
              padding: '10px 14px',
              backgroundColor: '#F9FAFB',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              fontFamily: 'monospace',
              fontSize: '13px',
              wordBreak: 'break-all',
              color: isMalicious ? '#B91C1C' : '#1F2937',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '16px', color: isMalicious ? '#DC2626' : '#16A34A' }}>
                {isMalicious ? 'link_off' : 'lock'}
              </span>
              <span>{result.url}</span>
            </div>
          </div>

          {/* Summary / Warning Section */}
          <div style={{
            padding: '14px 16px',
            borderRadius: '10px',
            backgroundColor: isMalicious ? '#FEF2F2' : '#F8FAFC',
            border: `1px solid ${isMalicious ? '#FECACA' : '#E2E8F0'}`,
          }}>
            <div style={{
              fontSize: '13.5px',
              fontWeight: 700,
              color: isMalicious ? '#991B1B' : '#334155',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              marginBottom: '6px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                {isMalicious ? 'warning' : 'info'}
              </span>
              <span>
                {isMalicious ? 'Security Advisory & Recommendation' : 'Probabilistic Model Assessment'}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: isMalicious ? '#7F1D1D' : '#475569', lineHeight: 1.5 }}>
              {isMalicious
                ? 'We recommend that you avoid opening or browsing to this website. The machine learning model identified technical patterns and character distributions strongly associated with phishing sites and credential stealing.'
                : 'No immediate malicious patterns were detected by the model. However, please remain cautious because machine learning classifications cannot guarantee complete safety.'}
            </p>
          </div>

          {/* Security Recommendations & Precautions */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {/* Recommendations */}
            <div style={{
              padding: '14px',
              backgroundColor: '#F9FAFB',
              borderRadius: '10px',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#7138E8' }}>security</span>
                <span>Recommended Action</span>
              </div>
              <ul style={{ paddingLeft: '18px', fontSize: '12.5px', color: '#4B5563', lineHeight: 1.5, margin: 0 }}>
                {(result.recommendations || []).map((rec, idx) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>{rec}</li>
                ))}
              </ul>
            </div>

            {/* Precautions */}
            <div style={{
              padding: '14px',
              backgroundColor: '#F9FAFB',
              borderRadius: '10px',
              border: '1px solid var(--border-color)',
            }}>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#7138E8' }}>tips_and_updates</span>
                <span>Security Precautions</span>
              </div>
              <ul style={{ paddingLeft: '18px', fontSize: '12.5px', color: '#4B5563', lineHeight: 1.5, margin: 0 }}>
                {(result.precautions || []).map((prec, idx) => (
                  <li key={idx} style={{ marginBottom: '4px' }}>{prec}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Action Row */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-color)',
          }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleClear}
              style={{ fontSize: '12.5px', padding: '8px 16px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>refresh</span>
              <span>Check Another Website</span>
            </button>

            {isMalicious && (
              <button
                type="button"
                onClick={handleReportScam}
                className="btn-danger"
                style={{ fontSize: '12.5px', padding: '8px 16px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>flag</span>
                <span>Report to Campus CyberAdmin</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
