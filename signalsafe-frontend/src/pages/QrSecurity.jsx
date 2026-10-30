import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import RiskScoreMeter from '../components/common/RiskScoreMeter';
import CameraModal from '../components/common/CameraModal';

export default function QrSecurity() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const isCyberAdmin = (user?.role || '').toUpperCase() === 'CYBERADMIN';

  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isCameraOpen, setIsCameraOpen] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setErrorMessage(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setErrorMessage(null);
    }
  };

  const handleCameraCapture = (file) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setErrorMessage(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMessage(null);
    try {
      const data = await api.analyzeQrCode(selectedFile);
      setResult(data);
    } catch (err) {
      console.error('QR Analysis error:', err);
      setErrorMessage(err.message || 'QR code decoding failed or server error occurred.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>
      {/* Live Webcam Modal */}
      <CameraModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCameraCapture}
        title="Live QR Code Scanner"
      />

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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>qr_code_scanner</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              QR Code Security Scanner
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Decode and inspect UPI QR codes to verify destination bank handles and detect tampered cafeteria standees.
            </p>
          </div>
        </div>
      </div>

      {/* Upload Dropzone Card */}
      <div className="erp-card">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {!previewUrl ? (
          <div>
            <div
              className="dropzone-area"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: '#F3E8FF',
                border: '1px solid #DDD6FE',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#7138E8',
                marginBottom: '12px',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>qr_code_2</span>
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#202124' }}>
                Upload or scan a QR code image
              </h3>
              <p style={{ fontSize: '13px', color: '#6B7280', marginTop: '4px' }}>
                Select an image file containing a payment QR code or scan using your device camera
              </p>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              marginTop: '18px',
              flexWrap: 'wrap',
            }}>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="btn-secondary"
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>folder_open</span>
                <span>Select QR Code File</span>
              </button>

              <button
                type="button"
                onClick={() => setIsCameraOpen(true)}
                className="btn-secondary"
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#7138E8' }}>photo_camera</span>
                <span>Scan Live with Camera</span>
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: '16px',
            }}>
              <div style={{
                maxWidth: '260px',
                maxHeight: '260px',
                overflow: 'hidden',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#F9FAFB',
                padding: '8px',
              }}>
                <img
                  src={previewUrl}
                  alt="QR Preview"
                  style={{ width: '100%', height: '100%', objectFit: 'contain', borderRadius: '8px' }}
                />
              </div>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={handleReset}
                  className="btn-secondary"
                  disabled={isAnalyzing}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>close</span>
                  <span>Choose Another QR</span>
                </button>

                <button
                  type="button"
                  onClick={handleAnalyze}
                  className="btn-primary"
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>sync</span>
                      <span>Decoding & Inspecting QR...</span>
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>qr_code_scanner</span>
                      <span>Analyze QR Destination</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
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

      {/* Results */}
      {result && <RiskScoreMeter result={result} />}

      {/* College QR Verification Card */}
      {result && result.college_verification && (() => {
        const cv = result.college_verification;
        const cls = cv.classification || result.classification;
        const isVerified = cls === 'VERIFIED_JCER_COLLEGE_QR';
        const isDiff = cls === 'KNOWN_COLLEGE_RECIPIENT_DETAILS_DIFFER';
        const isUnregistered = cls === 'OTHER_UPI_QR_NOT_REGISTERED';
        const isSuspicious = cls === 'SUSPICIOUS_OR_UNSAFE_QR';
        const isInactive = cls === 'NO_ACTIVE_COLLEGE_REGISTRY';
        const isDecodingFailed = cls === 'DECODING_FAILED' || cls === 'UNABLE_TO_VERIFY' || result.status === 'insufficient_evidence';

        let badgeConfig = {
          label: 'Unable to Verify',
          icon: 'help',
          color: '#4B5563',
          bg: '#F9FAFB',
          border: '#E5E7EB',
          headerBg: '#F3F4F6',
        };

        if (isDecodingFailed) {
          badgeConfig = {
            label: 'Decoding Failed / Unreadable',
            icon: 'search_off',
            color: '#4B5563',
            bg: '#F9FAFB',
            border: '#E5E7EB',
            headerBg: '#F3F4F6',
          };
        } else if (isVerified) {
          badgeConfig = {
            label: 'Official JCER College QR Verified',
            icon: 'verified',
            color: '#15803D',
            bg: '#F0FDF4',
            border: '#BBF7D0',
            headerBg: '#DCFCE7',
          };
        } else if (isDiff) {
          badgeConfig = {
            label: 'Known Recipient — Details Differ',
            icon: 'warning',
            color: '#B45309',
            bg: '#FFFBEB',
            border: '#FDE68A',
            headerBg: '#FEF3C7',
          };
        } else if (isUnregistered) {
          badgeConfig = {
            label: 'Valid External UPI QR (Not Registered)',
            icon: 'storefront',
            color: '#1D4ED8',
            bg: '#EFF6FF',
            border: '#BFDBFE',
            headerBg: '#DBEAFE',
          };
        } else if (isSuspicious) {
          badgeConfig = {
            label: 'High Risk / Threat Detected',
            icon: 'gpp_bad',
            color: '#B91C1C',
            bg: '#FEF2F2',
            border: '#FECACA',
            headerBg: '#FEE2E2',
          };
        } else if (isInactive) {
          badgeConfig = {
            label: 'College Registry Inactive',
            icon: 'info',
            color: '#475569',
            bg: '#F8FAFC',
            border: '#E2E8F0',
            headerBg: '#F1F5F9',
          };
        }

        const upiPa = result.payment_to || cv.expected_upi_id || '';
        const upiPn = result.payee_name || '';
        const upiAm = result.amount ? `₹${result.amount}` : (result.extracted_fields?.['Amount'] || 'Any');

        return (
          <div className="erp-card" style={{ marginTop: '20px' }}>
            {/* Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              paddingBottom: '16px',
              borderBottom: '1px solid var(--border-color)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  backgroundColor: '#F3E8FF',
                  border: '1px solid #DDD6FE',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#7138E8',
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>
                    verified_user
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#202124', margin: 0 }}>
                    College QR Verification
                  </h3>
                  <span style={{ fontSize: '12px', color: '#6B7280' }}>
                    Authoritative cross-check against official JCER CyberAdmin payment registry
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{
                  fontSize: '11.5px',
                  fontWeight: 700,
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-full)',
                  backgroundColor: badgeConfig.bg,
                  color: badgeConfig.color,
                  border: `1px solid ${badgeConfig.border}`,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>
                    {badgeConfig.icon}
                  </span>
                  <span>{badgeConfig.label}</span>
                </span>

                {isCyberAdmin && (
                  <button
                    type="button"
                    onClick={() => navigate('/admin/college-qr')}
                    className="btn-secondary"
                    style={{ fontSize: '12px', padding: '5px 10px', display: 'flex', alignItems: 'center', gap: '5px' }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '15px' }}>settings</span>
                    <span>Manage Registry</span>
                  </button>
                )}
              </div>
            </div>

            {/* Status Summary Banner */}
            <div style={{
              marginTop: '16px',
              padding: '14px 18px',
              borderRadius: '10px',
              backgroundColor: badgeConfig.bg,
              border: `1px solid ${badgeConfig.border}`,
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px', color: badgeConfig.color }}>
                  {badgeConfig.icon}
                </span>
                <strong style={{ fontSize: '14px', color: badgeConfig.color }}>
                  {cv.heading || 'Registry Analysis'}
                </strong>
              </div>
              <p style={{ fontSize: '13px', color: '#374151', margin: 0, lineHeight: 1.5 }}>
                {cv.explanation || 'No detailed explanation available.'}
              </p>
            </div>

            {/* Actionable Guidance on Decoding Failure */}
            {isDecodingFailed && (
              <div style={{
                marginTop: '16px',
                padding: '14px 18px',
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '10px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#374151', fontWeight: 600, fontSize: '13px' }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#7138E8' }}>tips_and_updates</span>
                  <span>Tips for Successfully Scanning QR Codes:</span>
                </div>
                <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12.5px', color: '#4B5563', lineHeight: 1.6 }}>
                  <li>Ensure the QR code has sufficient, even lighting with no harsh reflection or deep shadows.</li>
                  <li>Support for both light-theme and dark-theme QR codes is automatically enabled.</li>
                  <li>Hold the camera steady and squarely centered on the QR standee.</li>
                  <li>If the image contains wide surrounding background, crop closer to the QR square and re-upload.</li>
                </ul>
              </div>
            )}

            {/* Registered Record Overview (if matched or known destination) */}
            {(cv.registered_display_name || cv.official_recipient_name || cv.department) && (
              <div style={{
                marginTop: '16px',
                padding: '14px',
                backgroundColor: '#F8FAFC',
                borderRadius: '10px',
                border: '1px solid #E2E8F0',
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
              }}>
                <div>
                  <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                    Registered Name
                  </span>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#1E293B', marginTop: '2px' }}>
                    {cv.registered_display_name || '–'}
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                    Payment Purpose
                  </span>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#7138E8', marginTop: '2px' }}>
                    {cv.payment_purpose || 'General / Fees'}
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                    Department / Unit
                  </span>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#1E293B', marginTop: '2px' }}>
                    {cv.department || 'Finance & Accounts Office'}
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: '11px', color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
                    Official Payee Name
                  </span>
                  <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#1E293B', marginTop: '2px' }}>
                    {cv.official_recipient_name || '–'}
                  </div>
                </div>
              </div>
            )}

            {/* Discrepancy Warnings (if any) */}
            {cv.differing_fields && cv.differing_fields.length > 0 && (
              <div style={{ marginTop: '16px' }}>
                <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#B45309', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
                  Identified Parameter Discrepancies
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {cv.differing_fields.map((diff, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: '10px 14px',
                        backgroundColor: '#FFFBEB',
                        border: '1px solid #FDE68A',
                        borderRadius: '8px',
                        fontSize: '12.5px',
                        color: '#92400E',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '10px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#D97706' }}>
                          warning
                        </span>
                        <span>
                          <strong>{diff.field}:</strong> Expected <code>{String(diff.expected)}</code>, observed <code>{String(diff.observed)}</code>
                        </span>
                      </div>
                      <span className="badge badge-warning" style={{ fontSize: '10.5px' }}>
                        MISMATCH
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Structured Comparison Table */}
            {(cv.expected_upi_id || cv.registry_match) && (
              <div style={{ marginTop: '20px' }}>
                <h4 style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#64748B',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  marginBottom: '10px',
                }}>
                  Registry Field Comparison
                </h4>
                <div style={{ overflowX: 'auto' }}>
                  <table className="erp-table" style={{ fontSize: '12.5px', width: '100%' }}>
                    <thead>
                      <tr>
                        <th>PARAMETER</th>
                        <th>OBSERVED IN SCANNED QR</th>
                        <th>OFFICIAL JCER REGISTRY RECORD</th>
                        <th style={{ textAlign: 'right' }}>STATUS</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Destination UPI ID</td>
                        <td><code>{upiPa || '–'}</code></td>
                        <td><code>{cv.expected_upi_id || cv.registry_match?.expected_upi_id || '–'}</code></td>
                        <td style={{ textAlign: 'right' }}>
                          {(upiPa.toLowerCase() === (cv.expected_upi_id || cv.registry_match?.expected_upi_id || '').toLowerCase()) ? (
                            <span className="badge badge-safe" style={{ fontSize: '11px' }}>MATCH</span>
                          ) : (
                            <span className="badge badge-danger" style={{ fontSize: '11px' }}>DIFFERENT</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Merchant / Payee Name</td>
                        <td>{upiPn || '–'}</td>
                        <td>{cv.official_recipient_name || cv.registry_match?.official_recipient_name || '–'}</td>
                        <td style={{ textAlign: 'right' }}>
                          {(!cv.differing_fields || cv.differing_fields.every(d => d.field !== 'Official Recipient Name')) ? (
                            <span className="badge badge-safe" style={{ fontSize: '11px' }}>MATCH</span>
                          ) : (
                            <span className="badge badge-warning" style={{ fontSize: '11px' }}>DISCREPANCY</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Amount</td>
                        <td>{upiAm}</td>
                        <td>
                          {cv.expected_amount != null
                            ? `₹${parseFloat(cv.expected_amount).toFixed(2)}`
                            : (cv.registry_match?.expected_amount != null
                              ? `₹${parseFloat(cv.registry_match.expected_amount).toFixed(2)}`
                              : 'Any (User Specified)')}
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          {(!cv.differing_fields || cv.differing_fields.every(d => d.field !== 'Amount')) ? (
                            <span className="badge badge-safe" style={{ fontSize: '11px' }}>VALID</span>
                          ) : (
                            <span className="badge badge-warning" style={{ fontSize: '11px' }}>DIFFERING</span>
                          )}
                        </td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Department</td>
                        <td>Inferred via Approved Registry</td>
                        <td>{cv.department || cv.registry_match?.department || '–'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <span className="badge badge-safe" style={{ fontSize: '11px' }}>RECORDED</span>
                        </td>
                      </tr>
                      <tr>
                        <td style={{ fontWeight: 600 }}>Payment Purpose</td>
                        <td>{result.extracted_fields?.['Transaction Note'] || 'General Transaction'}</td>
                        <td>{cv.payment_purpose || cv.registry_match?.payment_purpose || '–'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <span className="badge badge-safe" style={{ fontSize: '11px' }}>RECORDED</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Mandatory Registry Notice */}
            <div style={{
              marginTop: '16px',
              padding: '12px 14px',
              borderRadius: '8px',
              backgroundColor: '#F8FAFC',
              border: '1px solid #E2E8F0',
              fontSize: '12px',
              color: '#64748B',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '8px',
              lineHeight: 1.5,
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '16px', color: '#7138E8', marginTop: '1px', flexShrink: 0 }}>
                info
              </span>
              <span>
                <strong>JCER Security Notice:</strong> {cv.registry_notice || 'This QR matches an active QR record approved by JCER CyberAdmin. This registry match does not independently prove bank-account ownership or confirm that a payment has occurred.'}
              </span>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
