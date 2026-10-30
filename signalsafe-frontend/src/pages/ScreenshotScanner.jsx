import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import RiskScoreMeter from '../components/common/RiskScoreMeter';
import CameraModal from '../components/common/CameraModal';

export default function ScreenshotScanner() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

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
      const data = await api.analyzeScreenshot(selectedFile);
      setResult(data);
    } catch (err) {
      console.error('Screenshot analysis error:', err);
      setErrorMessage(err.message || 'Payment screenshot analysis failed.');
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

  const getClassificationMeta = (classification) => {
    switch (classification) {
      case 'REFERENCE_DATASET_MATCH':
      case 'MATCHING_DEMO_RECORD':
        return {
          label: 'Reference Dataset Match',
          badgeText: 'MATCH FOUND',
          bg: '#F0FDF4',
          color: '#15803D',
          border: '#BBF7D0',
          icon: 'verified',
        };
      case 'RECIPIENT_NAME_MISMATCH':
      case 'DETAILS_MISMATCH':
        return {
          label: 'Recipient Name Mismatch — Manual Verification Recommended',
          badgeText: 'NAME MISMATCH',
          bg: '#FEF2F2',
          color: '#DC2626',
          border: '#FECACA',
          icon: 'warning',
        };
      case 'NO_MATCHING_RECORD':
        return {
          label: 'No Matching Reference Record',
          badgeText: 'UTR NOT FOUND',
          bg: '#F8FAFC',
          color: '#475569',
          border: '#E2E8F0',
          icon: 'help_outline',
        };
      case 'UNABLE_TO_VERIFY_OCR_UNCERTAIN':
      case 'INSUFFICIENT_INFORMATION':
        return {
          label: 'Unable to Verify — OCR Uncertain',
          badgeText: 'OCR UNCERTAIN',
          bg: '#FEF3C7',
          color: '#B45309',
          border: '#FCD34D',
          icon: 'error_outline',
        };
      case 'AMBIGUOUS_DATASET_RECORD':
        return {
          label: 'Ambiguous Dataset Record',
          badgeText: 'AMBIGUOUS RECORD',
          bg: '#FFFBEB',
          color: '#D97706',
          border: '#FDE68A',
          icon: 'warning',
        };
      case 'PARTIAL_MATCH':
        return {
          label: 'Partial Reference Match',
          badgeText: 'PARTIAL MATCH',
          bg: '#FFFBEB',
          color: '#D97706',
          border: '#FDE68A',
          icon: 'warning',
        };
      case 'NO_ACTIVE_DATASET':
      default:
        return {
          label: 'No Active Reference Dataset',
          badgeText: 'NO DATASET ACTIVE',
          bg: '#F3F4F6',
          color: '#4B5563',
          border: '#E5E7EB',
          icon: 'cloud_off',
        };
    }
  };

  const meta = result ? getClassificationMeta(result.classification) : null;
  const extracted = result?.extracted_fields || {};

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Live Webcam Modal */}
      <CameraModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={handleCameraCapture}
        title="Live Payment Receipt Camera"
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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>image_search</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              Payment Screenshot Verification
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Verify UPI receipt details against the active campus reference dataset with OCR and computer vision.
            </p>
          </div>
        </div>
      </div>

      {/* Main Upload Card */}
      <div className="erp-card">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
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
              style={{ cursor: 'pointer', padding: '36px 20px', textAlign: 'center' }}
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
                <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>receipt_long</span>
              </div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#202124' }}>
                Upload payment receipt screenshot
              </h3>
              <p style={{ fontSize: '13px', color: '#6B7280', marginTop: '4px' }}>
                Drag and drop image here, or browse files (Supports PNG, JPG, JPEG up to 15MB)
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
                <span>Browse Files</span>
              </button>

              <button
                type="button"
                onClick={() => setIsCameraOpen(true)}
                className="btn-secondary"
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#7138E8' }}>photo_camera</span>
                <span>Scan Receipt with Camera</span>
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
                maxWidth: '300px',
                maxHeight: '340px',
                overflow: 'hidden',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                backgroundColor: '#F9FAFB',
                padding: '8px',
              }}>
                <img
                  src={previewUrl}
                  alt="Receipt Preview"
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
                  <span>Choose Another Image</span>
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
                      <span>Extracting OCR & Matching Dataset...</span>
                    </>
                  ) : (
                    <>
                      <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>analytics</span>
                      <span>Verify Receipt Against Dataset</span>
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

      {/* Results Display */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Mandatory Demonstration Data Banner */}
          <div style={{
            padding: '14px 18px',
            backgroundColor: '#FFFBEB',
            border: '1px solid #FDE68A',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '22px', color: '#D97706', marginTop: '1px' }}>
              warning
            </span>
            <div style={{ fontSize: '13px', color: '#92400E', lineHeight: '1.5' }}>
              <strong>DEMO DATA — NOT BANK VERIFIED:</strong> Verification results reflect comparison against the active campus demonstration reference dataset. 
              Matching records confirm presence in the demonstration dataset, <strong>not real-time bank core payment confirmation</strong>.
            </div>
          </div>

          {/* Reference Dataset Match Decision Card */}
          <div className="erp-card" style={{ borderLeft: `5px solid ${meta.color}` }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              paddingBottom: '14px',
              borderBottom: '1px solid var(--border-color)',
              marginBottom: '14px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '50%',
                  backgroundColor: meta.bg,
                  border: `1px solid ${meta.border}`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: meta.color,
                }}>
                  <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>
                    {meta.icon}
                  </span>
                </div>
                <div>
                  <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#202124' }}>
                    {result.heading || meta.label}
                  </h2>
                  <div style={{ fontSize: '12px', color: '#6B7280', marginTop: '2px' }}>
                    {result.dataset_match?.match_method ? `Method: ${result.dataset_match.match_method}` : 'Dataset Matching Engine'}
                    {result.dataset_match?.dataset_version ? ` • Reference Dataset v${result.dataset_match.dataset_version}` : ''}
                  </div>
                </div>
              </div>

              <span style={{
                padding: '4px 12px',
                borderRadius: '9999px',
                backgroundColor: meta.bg,
                color: meta.color,
                border: `1px solid ${meta.border}`,
                fontSize: '12px',
                fontWeight: 700,
                letterSpacing: '0.03em',
              }}>
                {meta.badgeText}
              </span>
            </div>

            <p style={{ fontSize: '13.5px', color: '#374151', lineHeight: '1.6', marginBottom: '14px' }}>
              {result.dataset_match?.message || result.evidence_summary}
            </p>

            {/* Mismatch Highlights if any */}
            {result.mismatches && result.mismatches.length > 0 && (
              <div style={{
                padding: '12px 16px',
                borderRadius: '8px',
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
                marginBottom: '16px',
              }}>
                <div style={{ fontSize: '12.5px', fontWeight: 700, color: '#DC2626', marginBottom: '6px' }}>
                  Discrepancies Detected Against Demonstration Record:
                </div>
                <ul style={{ margin: '0 0 0 18px', fontSize: '13px', color: '#B91C1C' }}>
                  {result.mismatches.map((m, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{m}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Primary Field Comparison Table (UTR and Recipient Name) */}
            {((result.primary_comparison && result.primary_comparison.length > 0) ||
              (result.comparison_fields && result.comparison_fields.length > 0)) && (
              <div style={{ marginTop: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#1F2937' }}>
                    Primary Decision Fields (Authoritative Dataset Verification):
                  </h4>
                  <span style={{ fontSize: '11px', color: '#6B7280', fontWeight: 500 }}>
                    Governs Match / Mismatch classification
                  </span>
                </div>

                <div style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                  <table style={{ width: '100%', fontSize: '12.5px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#18181B', color: '#FFFFFF', textAlign: 'left' }}>
                        <th style={{ padding: '8px 12px' }}>Primary Field</th>
                        <th style={{ padding: '8px 12px' }}>Screenshot Extracted</th>
                        <th style={{ padding: '8px 12px' }}>Active Dataset Record</th>
                        <th style={{ padding: '8px 12px', textAlign: 'center' }}>Verification Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(result.primary_comparison || result.comparison_fields.filter(f => !f.is_informational)).map((f, i) => {
                        const isMatch = f.matched;
                        const isUncertain = f.result === 'OCR Uncertain';
                        const isNoMatch = f.result === 'No Match';
                        const isAmbiguous = f.result === 'Ambiguous';

                        let badgeBg = '#FEF2F2';
                        let badgeColor = '#DC2626';
                        let badgeBorder = '#FECACA';
                        let badgeIcon = 'cancel';
                        let badgeLabel = f.result || 'Mismatch';

                        if (isMatch) {
                          badgeBg = '#F0FDF4';
                          badgeColor = '#16A34A';
                          badgeBorder = '#BBF7D0';
                          badgeIcon = 'check_circle';
                          badgeLabel = 'Match';
                        } else if (isUncertain) {
                          badgeBg = '#FEF3C7';
                          badgeColor = '#B45309';
                          badgeBorder = '#FCD34D';
                          badgeIcon = 'help_outline';
                          badgeLabel = 'OCR Uncertain';
                        } else if (isNoMatch) {
                          badgeBg = '#F3F4F6';
                          badgeColor = '#4B5563';
                          badgeBorder = '#E5E7EB';
                          badgeIcon = 'search_off';
                          badgeLabel = 'Not In Dataset';
                        } else if (isAmbiguous) {
                          badgeBg = '#FFFBEB';
                          badgeColor = '#D97706';
                          badgeBorder = '#FDE68A';
                          badgeIcon = 'warning';
                          badgeLabel = 'Ambiguous';
                        }

                        return (
                          <tr key={i} style={{
                            borderBottom: '1px solid #E5E7EB',
                            backgroundColor: isMatch ? '#FFFFFF' : '#FFFDF7',
                          }}>
                            <td style={{ padding: '9px 12px', fontWeight: 700, color: '#111827' }}>
                              {f.field}
                            </td>
                            <td style={{
                              padding: '9px 12px',
                              fontFamily: f.field.includes('UTR') || f.field.includes('ID') ? 'monospace' : 'inherit',
                              fontWeight: 600,
                            }}>
                              {f.screenshot_value || '—'}
                            </td>
                            <td style={{
                              padding: '9px 12px',
                              fontFamily: f.field.includes('UTR') || f.field.includes('ID') ? 'monospace' : 'inherit',
                              color: f.dataset_value === '—' ? '#9CA3AF' : '#111827',
                            }}>
                              {f.dataset_value || '—'}
                            </td>
                            <td style={{ padding: '9px 12px', textAlign: 'center' }}>
                              <span style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                                padding: '2px 8px',
                                borderRadius: '9999px',
                                backgroundColor: badgeBg,
                                color: badgeColor,
                                border: `1px solid ${badgeBorder}`,
                                fontSize: '11px',
                                fontWeight: 700,
                              }}>
                                <span className="material-symbols-outlined" style={{ fontSize: '13px' }}>{badgeIcon}</span>
                                {badgeLabel}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Informational Receipt Fields (Separate section, not evaluated for primary matching) */}
            {((result.informational_fields && result.informational_fields.length > 0) ||
              (result.comparison_fields && result.comparison_fields.some(f => f.is_informational))) && (
              <div style={{
                marginTop: '18px',
                padding: '12px 14px',
                backgroundColor: '#F9FAFB',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h4 style={{ fontSize: '12.5px', fontWeight: 700, color: '#4B5563' }}>
                    Informational Receipt Fields (Not evaluated for primary matching decision):
                  </h4>
                  <span style={{ fontSize: '11px', color: '#6B7280' }}>
                    Informational only — does not affect verification decision
                  </span>
                </div>

                <div style={{ overflowX: 'auto', border: '1px solid #E5E7EB', borderRadius: '6px', backgroundColor: '#FFFFFF' }}>
                  <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#F3F4F6', color: '#4B5563', textAlign: 'left', borderBottom: '1px solid #E5E7EB' }}>
                        <th style={{ padding: '6px 10px', fontWeight: 600 }}>Informational Field</th>
                        <th style={{ padding: '6px 10px', fontWeight: 600 }}>Screenshot Extracted</th>
                        <th style={{ padding: '6px 10px', fontWeight: 600 }}>Active Dataset Record</th>
                        <th style={{ padding: '6px 10px', fontWeight: 600, textAlign: 'center' }}>Role</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(result.informational_fields || result.comparison_fields.filter(f => f.is_informational)).map((f, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid #F3F4F6' }}>
                          <td style={{ padding: '6px 10px', fontWeight: 600, color: '#4B5563' }}>{f.field}</td>
                          <td style={{ padding: '6px 10px', fontFamily: f.field.includes('ID') ? 'monospace' : 'inherit', color: '#1F2937' }}>
                            {f.screenshot_value || '—'}
                          </td>
                          <td style={{ padding: '6px 10px', fontFamily: f.field.includes('ID') ? 'monospace' : 'inherit', color: '#4B5563' }}>
                            {f.dataset_value || '—'}
                          </td>
                          <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                            <span style={{
                              padding: '1px 6px',
                              borderRadius: '4px',
                              backgroundColor: '#F3F4F6',
                              color: '#6B7280',
                              fontSize: '10.5px',
                              fontWeight: 600,
                            }}>
                              Informational
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Actionable Guidance Note */}
            {(result.classification === 'UNABLE_TO_VERIFY_OCR_UNCERTAIN' ||
              result.classification === 'INSUFFICIENT_INFORMATION') && (
              <div style={{
                marginTop: '14px',
                padding: '10px 14px',
                backgroundColor: '#FFFBEB',
                border: '1px solid #FDE68A',
                borderRadius: '8px',
                fontSize: '12.5px',
                color: '#92400E',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>tips_and_updates</span>
                <span>
                  <strong>Actionable Guidance:</strong> The UTR / bank reference number could not be read with high confidence.
                  Please re-upload a clean, uncropped screenshot or inspect the original receipt in your payment app.
                </span>
              </div>
            )}

            {result.classification === 'NO_MATCHING_RECORD' && (
              <div style={{
                marginTop: '14px',
                padding: '10px 14px',
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: '8px',
                fontSize: '12.5px',
                color: '#475569',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>info</span>
                <span>
                  <strong>Guidance:</strong> This UTR was not found in the active demonstration dataset.
                  This does not alone prove fraudulent intent; verify with the college finance desk or physical accounts register.
                </span>
              </div>
            )}

            {result.classification === 'RECIPIENT_NAME_MISMATCH' && (
              <div style={{
                marginTop: '14px',
                padding: '10px 14px',
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
                borderRadius: '8px',
                fontSize: '12.5px',
                color: '#991B1B',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>warning</span>
                <span>
                  <strong>Guidance:</strong> The transaction reference exists, but the payee differs from the authorized institution name.
                  Review the payee account carefully before accepting this receipt.
                </span>
              </div>
            )}
          </div>

          {/* Extracted Receipt Details Grid */}
          <div className="erp-card">
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              paddingBottom: '14px',
              borderBottom: '1px solid var(--border-color)',
              marginBottom: '14px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#7138E8' }}>
                document_scanner
              </span>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#202124' }}>
                Extracted Receipt Information
              </h3>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '12px',
            }}>
              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Transaction Amount
                </span>
                <span style={{ fontSize: '15px', fontWeight: 800, color: '#16A34A', marginTop: '2px', display: 'block' }}>
                  {extracted.amount ? `₹${extracted.amount}` : 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  UTR / Bank RRN
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '2px', display: 'block', fontFamily: 'monospace' }}>
                  {extracted.utr_rrn || 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Transaction ID
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '2px', display: 'block', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                  {extracted.transaction_id || 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Recipient / Payee
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '2px', display: 'block' }}>
                  {extracted.payee_name || 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Recipient UPI ID / VPA
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#7138E8', marginTop: '2px', display: 'block', wordBreak: 'break-all' }}>
                  {extracted.payee_vpa || 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Date & Time
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '2px', display: 'block' }}>
                  {[extracted.transaction_date, extracted.transaction_time].filter(Boolean).join(' at ') || 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Bank / UPI Application
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '2px', display: 'block' }}>
                  {extracted.bank_or_app_label || 'Not Detected'}
                </span>
              </div>

              <div style={{ padding: '10px 14px', backgroundColor: '#F8F9FD', borderRadius: '8px', border: '1px solid #E5EAF1' }}>
                <span style={{ fontSize: '10.5px', color: '#6B7280', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                  Payer Account
                </span>
                <span style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '2px', display: 'block', fontFamily: 'monospace' }}>
                  {extracted.payer_account_masked || 'Not Detected'}
                </span>
              </div>
            </div>
          </div>

          {/* Risk Score & Secondary Indicators */}
          <RiskScoreMeter result={result} />
        </div>
      )}
    </div>
  );
}
