import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function CyberAdminDatasetManagement() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // Active dataset state
  const [activeDataset, setActiveDataset] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Upload & validation state
  const [selectedFile, setSelectedFile] = useState(null);
  const [datasetNameInput, setDatasetNameInput] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [isActivating, setIsActivating] = useState(false);

  // Modals
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [showDeactivateModal, setShowDeactivateModal] = useState(false);

  const fetchDatasetData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const activeData = await api.getActiveScreenshotDataset();
      setActiveDataset(activeData);

      const historyData = await api.getScreenshotDatasetHistory();
      setHistory(historyData?.history || []);
    } catch (err) {
      console.error('Failed to fetch dataset data:', err);
      setErrorMessage(err.message || 'Unable to retrieve dataset configuration.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasetData();
  }, []);

  const handleFileSelect = async (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Only CSV (.csv) reference datasets are supported.');
      return;
    }
    setSelectedFile(file);
    setErrorMessage(null);
    setSuccessMessage(null);
    setValidationResult(null);

    // Auto validate upon selection
    setIsValidating(true);
    try {
      const val = await api.validateScreenshotDataset(file);
      setValidationResult(val);
      if (!datasetNameInput && file.name) {
        const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
        setDatasetNameInput(cleanName);
      }
    } catch (err) {
      console.error('Validation error:', err);
      setErrorMessage(err.message || 'CSV validation failed.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleActivateConfirmed = async () => {
    if (!selectedFile) return;
    setShowConfirmModal(false);
    setIsActivating(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const result = await api.activateScreenshotDataset(selectedFile, datasetNameInput.trim());
      setSuccessMessage(result.message || 'Dataset successfully activated as active reference.');
      setSelectedFile(null);
      setValidationResult(null);
      setDatasetNameInput('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      await fetchDatasetData();
    } catch (err) {
      console.error('Activation failed:', err);
      setErrorMessage(err.message || 'Failed to activate dataset.');
    } finally {
      setIsActivating(false);
    }
  };

  const handleDeactivateConfirmed = async () => {
    setShowDeactivateModal(false);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const res = await api.deactivateScreenshotDataset();
      setSuccessMessage(res.message || 'Dataset successfully deactivated.');
      await fetchDatasetData();
    } catch (err) {
      console.error('Deactivation error:', err);
      setErrorMessage(err.message || 'Failed to deactivate dataset.');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%' }}>
      {/* Navigation & Header */}
      <div>
        <button
          onClick={() => navigate('/cyberadmin')}
          className="btn-secondary"
          style={{ marginBottom: '14px', padding: '6px 12px', fontSize: '12.5px' }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>arrow_back</span>
          <span>Back to CyberAdmin Dashboard</span>
        </button>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '12px',
              backgroundColor: '#F3E8FF',
              border: '1px solid #DDD6FE',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#7138E8',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '26px' }}>dataset</span>
            </div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
                Screenshot Reference Dataset Management
              </h1>
              <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
                Configure and activate reference transaction datasets used by the campus Screenshot Scam Detector.
              </p>
            </div>
          </div>

          <button
            onClick={fetchDatasetData}
            disabled={isLoading}
            className="btn-secondary"
            style={{ padding: '8px 14px', fontSize: '13px' }}
          >
            <span className={`material-symbols-outlined ${isLoading ? 'spin-icon' : ''}`} style={{ fontSize: '16px' }}>
              sync
            </span>
            <span>Refresh Datasets</span>
          </button>
        </div>
      </div>

      {/* Mandatory Demo Data Notice Banner */}
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
          <strong>DEMO DATA NOTICE:</strong> SignalSafe Campus currently utilizes synthetic demonstration reference datasets because direct bank core banking systems (CBS) verification is not accessible in this demonstration environment. 
          Matching records indicate alignment with the uploaded campus demonstration dataset, <strong>not real-time bank payment verification</strong>.
        </div>
      </div>

      {/* Alerts */}
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

      {successMessage && (
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
          <span>{successMessage}</span>
        </div>
      )}

      {/* SECTION 1: Active Reference Dataset Overview */}
      <div className="erp-card">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          marginBottom: '20px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#7138E8' }}>
              verified
            </span>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#202124' }}>
              Currently Active Reference Dataset
            </h2>
          </div>

          {activeDataset?.active ? (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '9999px',
              backgroundColor: '#F0FDF4',
              color: '#15803D',
              border: '1px solid #BBF7D0',
              fontSize: '12px',
              fontWeight: 700,
            }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#16A34A' }} />
              ACTIVE (v{activeDataset.version})
            </span>
          ) : (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: '9999px',
              backgroundColor: '#F3F4F6',
              color: '#4B5563',
              border: '1px solid #E5E7EB',
              fontSize: '12px',
              fontWeight: 700,
            }}>
              NO ACTIVE DATASET
            </span>
          )}
        </div>

        {activeDataset?.active ? (
          <div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              marginBottom: '20px',
            }}>
              <div style={{ padding: '14px', backgroundColor: '#F8F9FD', borderRadius: '10px', border: '1px solid #E5EAF1' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280', textTransform: 'uppercase' }}>Dataset Name</div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#202124', marginTop: '4px' }}>
                  {activeDataset.dataset_name}
                </div>
                <div style={{ fontSize: '12px', color: '#7138E8', marginTop: '2px' }}>{activeDataset.filename}</div>
              </div>

              <div style={{ padding: '14px', backgroundColor: '#F8F9FD', borderRadius: '10px', border: '1px solid #E5EAF1' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280', textTransform: 'uppercase' }}>Total Records</div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: '#7138E8', marginTop: '4px' }}>
                  {activeDataset.total_records} Records
                </div>
                <div style={{ fontSize: '12px', color: '#16A34A', marginTop: '2px' }}>Indexed & Ready for OCR Matching</div>
              </div>

              <div style={{ padding: '14px', backgroundColor: '#F8F9FD', borderRadius: '10px', border: '1px solid #E5EAF1' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280', textTransform: 'uppercase' }}>Activated At</div>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#202124', marginTop: '4px' }}>
                  {new Date(activeDataset.activated_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })}
                </div>
                <div style={{ fontSize: '12px', color: '#6B7280', marginTop: '2px' }}>By: {activeDataset.uploaded_by}</div>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => setShowDeactivateModal(true)}
                className="btn-secondary"
                style={{ color: '#DC2626', borderColor: '#FECACA' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>block</span>
                <span>Deactivate Current Dataset</span>
              </button>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '30px 20px', color: '#6B7280' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#9CA3AF', marginBottom: '8px' }}>
              cloud_off
            </span>
            <p style={{ fontSize: '14px', fontWeight: 600, color: '#374151' }}>No reference dataset is currently active.</p>
            <p style={{ fontSize: '12.5px', marginTop: '4px' }}>
              Upload and activate a CSV dataset below so that student and faculty payment screenshots can be verified against reference records.
            </p>
          </div>
        )}
      </div>

      {/* SECTION 2: Upload & Validate New Reference Dataset */}
      <div className="erp-card">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          marginBottom: '20px',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#7138E8' }}>
            upload_file
          </span>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#202124' }}>
              Upload New Reference Dataset
            </h2>
            <p style={{ fontSize: '12.5px', color: '#6B7280' }}>
              Upload a UTF-8 CSV file containing reference transaction details. Activating will atomically supersede any active dataset.
            </p>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          style={{ display: 'none' }}
          onChange={(e) => handleFileSelect(e.target.files?.[0])}
        />

        {!selectedFile ? (
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
                <span className="material-symbols-outlined" style={{ fontSize: '26px' }}>file_upload</span>
              </div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#202124' }}>
                Click to browse or drag and drop reference CSV
              </h3>
              <p style={{ fontSize: '12.5px', color: '#6B7280', marginTop: '4px' }}>
                Required columns: transaction_id, utr_rrn, amount_inr, payee_name (up to 10MB)
              </p>
            </div>
          </div>
        ) : (
          <div>
            {/* File Info Bar */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 16px',
              backgroundColor: '#F8F9FD',
              borderRadius: '10px',
              border: '1px solid #E5EAF1',
              marginBottom: '20px',
              flexWrap: 'wrap',
              gap: '12px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '28px', color: '#7138E8' }}>
                  description
                </span>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#202124' }}>{selectedFile.name}</div>
                  <div style={{ fontSize: '12px', color: '#6B7280' }}>
                    {(selectedFile.size / 1024).toFixed(1)} KB • CSV Document
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedFile(null);
                    setValidationResult(null);
                    if (fileInputRef.current) fileInputRef.current.value = '';
                  }}
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12.5px' }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>close</span>
                  <span>Change File</span>
                </button>
              </div>
            </div>

            {/* Optional Dataset Name */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>
                Dataset Display Name (Optional)
              </label>
              <input
                type="text"
                value={datasetNameInput}
                onChange={(e) => setDatasetNameInput(e.target.value)}
                placeholder="e.g., Campus Fees & Cafeteria Reference Dataset 2026"
                className="input-field"
                style={{ width: '100%', maxWidth: '540px' }}
              />
            </div>

            {/* Validation Feedback */}
            {isValidating && (
              <div style={{ padding: '20px', textAlign: 'center', color: '#7138E8', fontSize: '13px' }}>
                <span className="material-symbols-outlined spin-icon" style={{ fontSize: '24px', verticalAlign: 'middle', marginRight: '8px' }}>
                  sync
                </span>
                Validating CSV headers, data types, and reference integrity...
              </div>
            )}

            {validationResult && (
              <div style={{ marginBottom: '24px' }}>
                <div style={{
                  padding: '14px 18px',
                  borderRadius: '10px',
                  backgroundColor: validationResult.is_valid ? '#F0FDF4' : '#FEF2F2',
                  border: `1px solid ${validationResult.is_valid ? '#BBF7D0' : '#FECACA'}`,
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span className="material-symbols-outlined" style={{
                      fontSize: '22px',
                      color: validationResult.is_valid ? '#16A34A' : '#DC2626',
                    }}>
                      {validationResult.is_valid ? 'check_circle' : 'error'}
                    </span>
                    <div>
                      <div style={{
                        fontSize: '14px',
                        fontWeight: 700,
                        color: validationResult.is_valid ? '#15803D' : '#991B1B',
                      }}>
                        {validationResult.is_valid ? 'CSV Validation Succeeded' : 'CSV Validation Failed'}
                      </div>
                      <div style={{ fontSize: '12px', color: validationResult.is_valid ? '#166534' : '#B91C1C' }}>
                        {validationResult.valid_count} valid records identified across {validationResult.total_rows} rows.
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '12px', fontSize: '12.5px' }}>
                    <span style={{ color: '#166534' }}>Valid: <strong>{validationResult.valid_count}</strong></span>
                    {validationResult.invalid_count > 0 && (
                      <span style={{ color: '#B91C1C' }}>Invalid: <strong>{validationResult.invalid_count}</strong></span>
                    )}
                    {validationResult.duplicate_count > 0 && (
                      <span style={{ color: '#D97706' }}>Duplicates: <strong>{validationResult.duplicate_count}</strong></span>
                    )}
                  </div>
                </div>

                {/* Warnings */}
                {validationResult.warnings && validationResult.warnings.length > 0 && (
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    backgroundColor: '#FFFBEB',
                    border: '1px solid #FDE68A',
                    fontSize: '12.5px',
                    color: '#92400E',
                    marginBottom: '16px',
                  }}>
                    <strong>Warnings:</strong>
                    <ul style={{ margin: '4px 0 0 18px' }}>
                      {validationResult.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Preview Table */}
                {validationResult.preview_records && validationResult.preview_records.length > 0 && (
                  <div style={{ marginTop: '14px' }}>
                    <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#374151', marginBottom: '8px' }}>
                      Preview (First {validationResult.preview_records.length} records):
                    </h4>
                    <div style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                      <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                        <thead>
                          <tr style={{ backgroundColor: '#18181B', color: '#FFFFFF', textAlign: 'left' }}>
                            <th style={{ padding: '8px 12px' }}>Record ID</th>
                            <th style={{ padding: '8px 12px' }}>Txn ID</th>
                            <th style={{ padding: '8px 12px' }}>UTR / RRN</th>
                            <th style={{ padding: '8px 12px' }}>Amount</th>
                            <th style={{ padding: '8px 12px' }}>Payee Name</th>
                            <th style={{ padding: '8px 12px' }}>Payee UPI ID</th>
                          </tr>
                        </thead>
                        <tbody>
                          {validationResult.preview_records.map((r, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid #E5E7EB', backgroundColor: i % 2 === 0 ? '#FFFFFF' : '#F9FAFB' }}>
                              <td style={{ padding: '8px 12px', fontWeight: 600 }}>{r.record_id}</td>
                              <td style={{ padding: '8px 12px', fontFamily: 'monospace' }}>{r.transaction_id || '—'}</td>
                              <td style={{ padding: '8px 12px', fontFamily: 'monospace' }}>{r.utr_rrn || '—'}</td>
                              <td style={{ padding: '8px 12px', fontWeight: 700, color: '#16A34A' }}>₹{r.amount_inr}</td>
                              <td style={{ padding: '8px 12px' }}>{r.payee_name}</td>
                              <td style={{ padding: '8px 12px', color: '#7138E8' }}>{r.payee_vpa || '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Activate Action Button */}
                {validationResult.is_valid && (
                  <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <button
                      type="button"
                      onClick={() => setShowConfirmModal(true)}
                      disabled={isActivating}
                      className="btn-primary"
                      style={{ padding: '10px 20px', fontSize: '14px' }}
                    >
                      {isActivating ? (
                        <>
                          <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>sync</span>
                          <span>Activating in PostgreSQL...</span>
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>check_circle</span>
                          <span>Activate Dataset as Active Reference</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* SECTION 3: Dataset Version History */}
      <div className="erp-card">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          marginBottom: '16px',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#7138E8' }}>
            history
          </span>
          <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#202124' }}>
            Reference Dataset Version History
          </h2>
        </div>

        {history && history.length > 0 ? (
          <div style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: '10px' }}>
            <table style={{ width: '100%', fontSize: '12.5px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#18181B', color: '#FFFFFF', textAlign: 'left' }}>
                  <th style={{ padding: '10px 14px' }}>Version</th>
                  <th style={{ padding: '10px 14px' }}>Dataset Name & Filename</th>
                  <th style={{ padding: '10px 14px' }}>Records</th>
                  <th style={{ padding: '10px 14px' }}>Uploaded By</th>
                  <th style={{ padding: '10px 14px' }}>Upload Date</th>
                  <th style={{ padding: '10px 14px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((ds) => (
                  <tr key={ds.id} style={{ borderBottom: '1px solid #E5E7EB', backgroundColor: ds.is_active ? '#F8F5FF' : '#FFFFFF' }}>
                    <td style={{ padding: '10px 14px', fontWeight: 700 }}>v{ds.version}</td>
                    <td style={{ padding: '10px 14px' }}>
                      <div style={{ fontWeight: 600, color: '#202124' }}>{ds.dataset_name}</div>
                      <div style={{ fontSize: '11.5px', color: '#6B7280' }}>{ds.filename}</div>
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 700 }}>{ds.total_records}</td>
                    <td style={{ padding: '10px 14px', color: '#4B5563' }}>{ds.uploaded_by}</td>
                    <td style={{ padding: '10px 14px', color: '#6B7280' }}>
                      {ds.created_at ? new Date(ds.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {ds.is_active ? (
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '9999px',
                          backgroundColor: '#F0FDF4',
                          color: '#15803D',
                          fontWeight: 700,
                          fontSize: '11px',
                          border: '1px solid #BBF7D0',
                        }}>
                          ACTIVE
                        </span>
                      ) : (
                        <span style={{
                          padding: '3px 8px',
                          borderRadius: '9999px',
                          backgroundColor: '#F3F4F6',
                          color: '#6B7280',
                          fontSize: '11px',
                          border: '1px solid #E5E7EB',
                        }}>
                          SUPERSEDED
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '24px', textAlign: 'center', color: '#6B7280', fontSize: '13px' }}>
            No past dataset versions recorded in the database.
          </div>
        )}
      </div>

      {/* Confirmation Modal for Activation */}
      {showConfirmModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(32, 33, 36, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px',
        }}>
          <div style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '14px',
            maxWidth: '520px',
            width: '100%',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#7138E8', marginBottom: '14px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '26px' }}>verified</span>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
                Confirm Dataset Activation
              </h3>
            </div>

            <p style={{ fontSize: '13.5px', color: '#4B5563', lineHeight: '1.5', marginBottom: '14px' }}>
              Activating <strong>{selectedFile?.name}</strong> will atomically replace the currently active reference dataset.
              All subsequent payment screenshot scans across the campus portal will be matched against these <strong>{validationResult?.valid_count} records</strong>.
            </p>

            <div style={{
              padding: '12px 14px',
              backgroundColor: '#FFFBEB',
              border: '1px solid #FDE68A',
              borderRadius: '8px',
              fontSize: '12px',
              color: '#92400E',
              marginBottom: '20px',
            }}>
              <strong>Demonstration Notice Reminder:</strong> All verification responses will include the explicit notice: <em>"DEMO DATA — NOT BANK VERIFIED"</em>.
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleActivateConfirmed}
                className="btn-primary"
              >
                Confirm & Activate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal for Deactivation */}
      {showDeactivateModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(32, 33, 36, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px',
        }}>
          <div style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '14px',
            maxWidth: '480px',
            width: '100%',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#DC2626', marginBottom: '14px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '26px' }}>warning</span>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
                Deactivate Reference Dataset?
              </h3>
            </div>

            <p style={{ fontSize: '13.5px', color: '#4B5563', lineHeight: '1.5', marginBottom: '20px' }}>
              Are you sure you want to deactivate dataset <strong>v{activeDataset?.version} ({activeDataset?.dataset_name})</strong>? 
              Users attempting to scan payment screenshots will see a notice that no active reference dataset is configured until a new one is activated.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setShowDeactivateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeactivateConfirmed}
                className="btn-danger"
              >
                Deactivate Dataset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

