import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

export default function CollegeQrManagement() {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Stats & List State
  const [stats, setStats] = useState(null);
  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Filters & Search
  const [search, setSearch] = useState('');
  const [selectedPurpose, setSelectedPurpose] = useState('ALL');
  const [selectedDepartment, setSelectedDepartment] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  // Single Registration Modal State
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [singleFile, setSingleFile] = useState(null);
  const [singlePreviewUrl, setSinglePreviewUrl] = useState(null);
  const [isDecoding, setIsDecoding] = useState(false);
  const [decodedData, setDecodedData] = useState(null);
  const [duplicateWarnings, setDuplicateWarnings] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form fields for registration
  const [displayName, setDisplayName] = useState('');
  const [paymentPurpose, setPaymentPurpose] = useState('Tuition Fees');
  const [department, setDepartment] = useState('Finance & Accounts Office');
  const [officialRecipient, setOfficialRecipient] = useState('');
  const [expectedUpiId, setExpectedUpiId] = useState('');
  const [expectedAmount, setExpectedAmount] = useState('');
  const [description, setDescription] = useState('');
  const [autoApprove, setAutoApprove] = useState(true);

  // Bulk Upload Modal State
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkPurpose, setBulkPurpose] = useState('Tuition Fees');
  const [bulkDepartment, setBulkDepartment] = useState('Finance & Accounts Office');
  const [bulkAutoApprove, setBulkAutoApprove] = useState(false);
  const [isBulkSubmitting, setIsBulkSubmitting] = useState(false);
  const [bulkResult, setBulkResult] = useState(null);

  // Action Modals
  const [inspectRecord, setInspectRecord] = useState(null);
  const [editRecord, setEditRecord] = useState(null);
  const [replaceRecord, setReplaceRecord] = useState(null);
  const [archiveTarget, setArchiveTarget] = useState(null);

  const singleFileInputRef = useRef(null);
  const bulkFileInputRef = useRef(null);
  const replaceFileInputRef = useRef(null);

  // Fetch Stats and Records
  const fetchRegistryData = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const statsData = await api.getCollegeQrStats();
      setStats(statsData);

      const listData = await api.listCollegeQrs({
        search,
        payment_purpose: selectedPurpose,
        department: selectedDepartment,
        approval_status: selectedStatus,
        page,
        page_size: pageSize,
      });

      setRecords(listData.records || []);
      setTotalCount(listData.total_count || 0);
      setTotalPages(listData.total_pages || 1);
    } catch (err) {
      console.error('Failed to fetch college QR data:', err);
      setErrorMessage(err.message || 'Unable to load college QR registry data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRegistryData();
  }, [page, selectedPurpose, selectedDepartment, selectedStatus]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchRegistryData();
  };

  // -------------------------------------------------------------
  // Single QR Upload & Decode Preview
  // -------------------------------------------------------------
  const handleSingleFileSelect = async (file) => {
    if (!file) return;
    setSingleFile(file);
    setSinglePreviewUrl(URL.createObjectURL(file));
    setDecodedData(null);
    setDuplicateWarnings([]);
    setIsDecoding(true);

    try {
      const preview = await api.previewCollegeQrDecode(file);
      if (!preview.success) {
        setErrorMessage(`QR Decoding Warning: ${preview.error}`);
      } else {
        setDecodedData(preview);
        setDuplicateWarnings(preview.warnings || []);

        const ext = preview.extracted_fields || {};
        if (ext.official_recipient_name && !officialRecipient) {
          setOfficialRecipient(ext.official_recipient_name);
        }
        if (ext.expected_upi_id && !expectedUpiId) {
          setExpectedUpiId(ext.expected_upi_id);
        }
        if (ext.expected_amount && !expectedAmount) {
          setExpectedAmount(ext.expected_amount);
        }
        if (!displayName) {
          const defaultName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ').title || 'JCER Payment Counter';
          setDisplayName(defaultName);
        }
      }
    } catch (err) {
      console.error('Preview decode error:', err);
      setErrorMessage(err.message || 'Could not decode QR code from the selected image.');
    } finally {
      setIsDecoding(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (!singleFile) {
      setErrorMessage('Please select a QR code image to upload.');
      return;
    }
    if (!displayName || !expectedUpiId || !officialRecipient) {
      setErrorMessage('Please fill in all required fields (Display Name, Expected UPI ID, Recipient Name).');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      await api.createCollegeQr({
        file: singleFile,
        display_name: displayName,
        payment_purpose: paymentPurpose,
        department,
        official_recipient_name: officialRecipient,
        expected_upi_id: expectedUpiId,
        expected_amount: expectedAmount ? parseFloat(expectedAmount) : null,
        description,
        auto_approve: autoApprove,
      });

      setSuccessMessage(`College QR record '${displayName}' registered successfully!`);
      setShowRegisterModal(false);
      resetRegisterForm();
      fetchRegistryData();
    } catch (err) {
      console.error('Registration error:', err);
      setErrorMessage(err.message || 'Failed to register college QR code.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetRegisterForm = () => {
    setSingleFile(null);
    setSinglePreviewUrl(null);
    setDecodedData(null);
    setDuplicateWarnings([]);
    setDisplayName('');
    setPaymentPurpose('Tuition Fees');
    setDepartment('Finance & Accounts Office');
    setOfficialRecipient('');
    setExpectedUpiId('');
    setExpectedAmount('');
    setDescription('');
    setAutoApprove(true);
    if (singleFileInputRef.current) singleFileInputRef.current.value = '';
  };

  // -------------------------------------------------------------
  // Bulk Upload Workflow
  // -------------------------------------------------------------
  const handleBulkUploadSubmit = async (e) => {
    e.preventDefault();
    if (!bulkFiles || bulkFiles.length === 0) {
      setErrorMessage('Please select one or more QR code image files.');
      return;
    }

    setIsBulkSubmitting(true);
    setErrorMessage(null);
    try {
      const res = await api.bulkUploadCollegeQrs(
        bulkFiles,
        bulkPurpose,
        bulkDepartment,
        bulkAutoApprove
      );
      setBulkResult(res);
      setSuccessMessage(`Bulk import processed: ${res.successful_count} successful, ${res.failed_count} failed.`);
      fetchRegistryData();
    } catch (err) {
      console.error('Bulk upload error:', err);
      setErrorMessage(err.message || 'Bulk upload failed.');
    } finally {
      setIsBulkSubmitting(false);
    }
  };

  // -------------------------------------------------------------
  // Record Actions: Approve, Deactivate, Reactivate, Archive
  // -------------------------------------------------------------
  const handleApprove = async (recordId) => {
    try {
      const res = await api.approveCollegeQr(recordId);
      setSuccessMessage(res.message);
      fetchRegistryData();
    } catch (err) {
      setErrorMessage(err.message || 'Approval failed.');
    }
  };

  const handleDeactivate = async (recordId) => {
    try {
      const res = await api.deactivateCollegeQr(recordId);
      setSuccessMessage(res.message);
      fetchRegistryData();
    } catch (err) {
      setErrorMessage(err.message || 'Deactivation failed.');
    }
  };

  const handleReactivate = async (recordId) => {
    try {
      const res = await api.approveCollegeQr(recordId); // Re-approves/activates
      setSuccessMessage(res.message);
      fetchRegistryData();
    } catch (err) {
      setErrorMessage(err.message || 'Reactivation failed.');
    }
  };

  const handleArchiveConfirm = async () => {
    if (!archiveTarget) return;
    try {
      const res = await api.archiveCollegeQr(archiveTarget.record_id);
      setSuccessMessage(res.message);
      setArchiveTarget(null);
      fetchRegistryData();
    } catch (err) {
      setErrorMessage(err.message || 'Archival failed.');
    }
  };

  const handleEditSave = async (e) => {
    e.preventDefault();
    if (!editRecord) return;
    try {
      const res = await api.updateCollegeQr(editRecord.record_id, {
        display_name: editRecord.display_name,
        payment_purpose: editRecord.payment_purpose,
        department: editRecord.department,
        official_recipient_name: editRecord.official_recipient_name,
        expected_amount: editRecord.expected_amount,
        description: editRecord.description,
      });
      setSuccessMessage(res.message);
      setEditRecord(null);
      fetchRegistryData();
    } catch (err) {
      setErrorMessage(err.message || 'Update failed.');
    }
  };

  const handleReplaceImage = async (file) => {
    if (!replaceRecord || !file) return;
    try {
      const res = await api.replaceCollegeQrImage(replaceRecord.record_id, file);
      setSuccessMessage(res.message);
      setReplaceRecord(null);
      fetchRegistryData();
    } catch (err) {
      setErrorMessage(err.message || 'Image replacement failed.');
    }
  };

  const purposesList = stats?.configured_purposes || [
    'Tuition Fees', 'Examination Fees', 'Hostel & Mess Fees', 'Library Dues & Deposits',
    'Transportation & Bus Pass', 'Cafeteria & Meal Service', 'Event Registration', 'Other Approved College Payment'
  ];

  const departmentsList = stats?.configured_departments || [
    'Finance & Accounts Office', 'Examination & Evaluation Cell', 'Hostel Administration',
    'Central Library', 'Transportation Department', 'Campus Cafeteria', 'Computer Science & Engineering'
  ];

  return (
    <div style={{ maxWidth: '1140px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
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
              <span className="material-symbols-outlined" style={{ fontSize: '28px' }}>qr_code_2</span>
            </div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
                College UPI QR Registry Management
              </h1>
              <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
                Manage authoritative official JCER payment QR codes used by the campus QR Code Security Scanner.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button
              onClick={() => {
                resetRegisterForm();
                setShowRegisterModal(true);
              }}
              className="btn-primary"
              style={{ padding: '8px 16px', fontSize: '13px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>add</span>
              <span>Register College QR</span>
            </button>

            <button
              onClick={() => {
                setBulkFiles([]);
                setBulkResult(null);
                setShowBulkModal(true);
              }}
              className="btn-secondary"
              style={{ padding: '8px 16px', fontSize: '13px' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>upload</span>
              <span>Bulk Upload QRs</span>
            </button>
          </div>
        </div>
      </div>

      {/* Advisory Notice Banner */}
      <div style={{
        padding: '12px 18px',
        backgroundColor: '#FFFBEB',
        border: '1px solid #FDE68A',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '12.5px',
        color: '#92400E',
      }}>
        <span className="material-symbols-outlined" style={{ fontSize: '20px', color: '#D97706', flexShrink: 0 }}>
          verified_user
        </span>
        <div>
          <strong>Authoritative College Reference Dataset:</strong> Approved records in this registry become the authoritative baseline for determining whether a scanned QR matches an officially registered JCER payment counter.
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

      {/* Registry Overview Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '14px',
      }}>
        <div className="erp-card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11.5px', fontWeight: 600, color: '#6B7280', textTransform: 'uppercase' }}>
            Total Registered
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#202124', marginTop: '4px' }}>
            {stats?.total_registered ?? '—'}
          </div>
          <div style={{ fontSize: '12px', color: '#7138E8', marginTop: '2px' }}>
            Across {stats?.departments_count ?? 0} Department(s)
          </div>
        </div>

        <div className="erp-card" style={{ padding: '16px', borderLeft: '4px solid #16A34A' }}>
          <div style={{ fontSize: '11.5px', fontWeight: 600, color: '#166534', textTransform: 'uppercase' }}>
            Active & Approved
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#16A34A', marginTop: '4px' }}>
            {stats?.active_approved ?? '—'}
          </div>
          <div style={{ fontSize: '12px', color: '#15803D', marginTop: '2px' }}>
            Enforced in QR Scanner
          </div>
        </div>

        <div className="erp-card" style={{ padding: '16px', borderLeft: '4px solid #D97706' }}>
          <div style={{ fontSize: '11.5px', fontWeight: 600, color: '#B45309', textTransform: 'uppercase' }}>
            Awaiting Approval
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#D97706', marginTop: '4px' }}>
            {stats?.awaiting_approval ?? '—'}
          </div>
          <div style={{ fontSize: '12px', color: '#92400E', marginTop: '2px' }}>
            Pending Admin Review
          </div>
        </div>

        <div className="erp-card" style={{ padding: '16px', borderLeft: '4px solid #6B7280' }}>
          <div style={{ fontSize: '11.5px', fontWeight: 600, color: '#4B5563', textTransform: 'uppercase' }}>
            Inactive / Paused
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#4B5563', marginTop: '4px' }}>
            {stats?.inactive ?? '—'}
          </div>
          <div style={{ fontSize: '12px', color: '#6B7280', marginTop: '2px' }}>
            Temporarily Disabled
          </div>
        </div>
      </div>

      {/* Main Registry Table & Filtering Card */}
      <div className="erp-card">
        {/* Filters Bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
          paddingBottom: '16px',
          borderBottom: '1px solid var(--border-color)',
          marginBottom: '16px',
        }}>
          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px', flex: 1, minWidth: '260px', maxWidth: '420px' }}>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by counter name, UPI ID, recipient, or record ID..."
              className="input-field"
              style={{ flex: 1, fontSize: '13px', padding: '8px 12px' }}
            />
            <button type="submit" className="btn-secondary" style={{ padding: '8px 12px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>search</span>
            </button>
          </form>

          {/* Filter Dropdowns */}
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <select
              value={selectedPurpose}
              onChange={(e) => {
                setSelectedPurpose(e.target.value);
                setPage(1);
              }}
              className="input-field"
              style={{ fontSize: '12.5px', padding: '6px 10px' }}
            >
              <option value="ALL">All Payment Purposes</option>
              {purposesList.map((p, idx) => (
                <option key={idx} value={p}>{p}</option>
              ))}
            </select>

            <select
              value={selectedDepartment}
              onChange={(e) => {
                setSelectedDepartment(e.target.value);
                setPage(1);
              }}
              className="input-field"
              style={{ fontSize: '12.5px', padding: '6px 10px' }}
            >
              <option value="ALL">All Departments</option>
              {departmentsList.map((d, idx) => (
                <option key={idx} value={d}>{d}</option>
              ))}
            </select>

            <select
              value={selectedStatus}
              onChange={(e) => {
                setSelectedStatus(e.target.value);
                setPage(1);
              }}
              className="input-field"
              style={{ fontSize: '12.5px', padding: '6px 10px' }}
            >
              <option value="ALL">All Statuses</option>
              <option value="APPROVED">Approved & Active</option>
              <option value="PENDING_APPROVAL">Pending Approval</option>
            </select>
          </div>
        </div>

        {/* Registry Table */}
        {isLoading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#7138E8', fontSize: '13.5px' }}>
            <span className="material-symbols-outlined spin-icon" style={{ fontSize: '26px', verticalAlign: 'middle', marginRight: '8px' }}>
              sync
            </span>
            Loading JCER College QR Registry...
          </div>
        ) : records.length > 0 ? (
          <div>
            <div style={{ overflowX: 'auto', border: '1px solid var(--border-color)', borderRadius: '10px' }}>
              <table style={{ width: '100%', fontSize: '12.5px', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#18181B', color: '#FFFFFF', textAlign: 'left' }}>
                    <th style={{ padding: '10px 14px' }}>Record ID & Name</th>
                    <th style={{ padding: '10px 14px' }}>Payment Purpose & Department</th>
                    <th style={{ padding: '10px 14px' }}>Official Recipient & UPI ID</th>
                    <th style={{ padding: '10px 14px' }}>Amount</th>
                    <th style={{ padding: '10px 14px' }}>Status</th>
                    <th style={{ padding: '10px 14px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((qr) => (
                    <tr key={qr.record_id} style={{
                      borderBottom: '1px solid #E5E7EB',
                      backgroundColor: qr.is_active ? '#FFFFFF' : '#F9FAFB',
                    }}>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ fontWeight: 700, color: '#202124' }}>{qr.display_name}</div>
                        <div style={{ fontSize: '11px', color: '#7138E8', fontFamily: 'monospace' }}>
                          {qr.record_id}
                        </div>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ fontWeight: 600, color: '#202124' }}>{qr.payment_purpose}</div>
                        <div style={{ fontSize: '11.5px', color: '#6B7280' }}>{qr.department || 'General Administration'}</div>
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        <div style={{ fontWeight: 600, color: '#202124' }}>{qr.official_recipient_name}</div>
                        <div style={{ fontSize: '11.5px', color: '#7138E8', fontFamily: 'monospace' }}>
                          {qr.expected_upi_id}
                        </div>
                      </td>
                      <td style={{ padding: '10px 14px', fontWeight: 700 }}>
                        {qr.expected_amount !== null && qr.expected_amount !== undefined ? (
                          <span style={{ color: '#16A34A' }}>₹{qr.expected_amount.toFixed(2)}</span>
                        ) : (
                          <span style={{ color: '#6B7280' }}>Variable</span>
                        )}
                      </td>
                      <td style={{ padding: '10px 14px' }}>
                        {qr.is_active && qr.approval_status === 'APPROVED' ? (
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '9999px',
                            backgroundColor: '#F0FDF4',
                            color: '#15803D',
                            border: '1px solid #BBF7D0',
                            fontSize: '11px',
                            fontWeight: 700,
                          }}>
                            ACTIVE
                          </span>
                        ) : qr.approval_status === 'PENDING_APPROVAL' ? (
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '9999px',
                            backgroundColor: '#FFFBEB',
                            color: '#B45309',
                            border: '1px solid #FDE68A',
                            fontSize: '11px',
                            fontWeight: 700,
                          }}>
                            PENDING REVIEW
                          </span>
                        ) : (
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '9999px',
                            backgroundColor: '#F3F4F6',
                            color: '#6B7280',
                            border: '1px solid #E5E7EB',
                            fontSize: '11px',
                            fontWeight: 700,
                          }}>
                            INACTIVE
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '10px 14px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '6px' }}>
                          <button
                            type="button"
                            onClick={() => setInspectRecord(qr)}
                            className="btn-secondary"
                            title="Inspect Details"
                            style={{ padding: '4px 8px' }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>visibility</span>
                          </button>

                          {qr.approval_status === 'PENDING_APPROVAL' ? (
                            <button
                              type="button"
                              onClick={() => handleApprove(qr.record_id)}
                              className="btn-primary"
                              title="Approve & Activate"
                              style={{ padding: '4px 8px', backgroundColor: '#16A34A' }}
                            >
                              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check_circle</span>
                            </button>
                          ) : qr.is_active ? (
                            <button
                              type="button"
                              onClick={() => handleDeactivate(qr.record_id)}
                              className="btn-secondary"
                              title="Deactivate QR"
                              style={{ padding: '4px 8px', color: '#D97706' }}
                            >
                              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>pause_circle</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleReactivate(qr.record_id)}
                              className="btn-secondary"
                              title="Reactivate QR"
                              style={{ padding: '4px 8px', color: '#16A34A' }}
                            >
                              <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>play_circle</span>
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => setEditRecord(qr)}
                            className="btn-secondary"
                            title="Edit Metadata"
                            style={{ padding: '4px 8px' }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>edit</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => setReplaceRecord(qr)}
                            className="btn-secondary"
                            title="Replace QR Image"
                            style={{ padding: '4px 8px', color: '#7138E8' }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>image</span>
                          </button>

                          <button
                            type="button"
                            onClick={() => setArchiveTarget(qr)}
                            className="btn-secondary"
                            title="Archive Record"
                            style={{ padding: '4px 8px', color: '#DC2626' }}
                          >
                            <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>archive</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '16px',
              fontSize: '12.5px',
              color: '#6B7280',
            }}>
              <div>
                Showing {records.length} of {totalCount} registered QR records (Page {page} of {totalPages})
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                >
                  Previous
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="btn-secondary"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: '#6B7280' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '48px', color: '#9CA3AF', marginBottom: '8px' }}>
              qr_code_2
            </span>
            <p style={{ fontSize: '15px', fontWeight: 600, color: '#374151' }}>No College Payment QRs Match Search Criteria</p>
            <p style={{ fontSize: '13px', marginTop: '4px' }}>
              Upload and register actual college payment QR codes above to populate the official reference registry.
            </p>
          </div>
        )}
      </div>

      {/* ========================================================= */}
      {/* MODAL 1: Register Single College QR Code                  */}
      {/* ========================================================= */}
      {showRegisterModal && (
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
            maxWidth: '640px',
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px', color: '#7138E8' }}>
                  add_photo_alternate
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
                  Register Official College Payment QR
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowRegisterModal(false)}
                className="btn-secondary"
                style={{ padding: '4px 8px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>close</span>
              </button>
            </div>

            <form onSubmit={handleRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* File Upload & Preview */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>
                  Payment QR Code Image *
                </label>
                <input
                  ref={singleFileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/webp"
                  style={{ display: 'none' }}
                  onChange={(e) => handleSingleFileSelect(e.target.files?.[0])}
                />

                {!singlePreviewUrl ? (
                  <div
                    onClick={() => singleFileInputRef.current?.click()}
                    style={{
                      border: '2px dashed #DDD6FE',
                      borderRadius: '10px',
                      padding: '24px',
                      textAlign: 'center',
                      backgroundColor: '#F8F5FF',
                      cursor: 'pointer',
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '32px', color: '#7138E8' }}>
                      upload_file
                    </span>
                    <div style={{ fontSize: '13px', fontWeight: 600, color: '#202124', marginTop: '4px' }}>
                      Click to select QR code image
                    </div>
                    <div style={{ fontSize: '11.5px', color: '#6B7280' }}>Supports PNG, JPG, JPEG (Max 10MB)</div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '10px', backgroundColor: '#F8F9FD', borderRadius: '10px', border: '1px solid #E5EAF1' }}>
                    <img
                      src={singlePreviewUrl}
                      alt="QR Preview"
                      style={{ width: '80px', height: '80px', objectFit: 'contain', borderRadius: '6px', backgroundColor: '#FFFFFF', border: '1px solid #E5E7EB' }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#202124' }}>{singleFile.name}</div>
                      <div style={{ fontSize: '11.5px', color: '#6B7280' }}>
                        {(singleFile.size / 1024).toFixed(1)} KB • {isDecoding ? 'Decoding QR...' : 'Decoded'}
                      </div>
                      <button
                        type="button"
                        onClick={() => singleFileInputRef.current?.click()}
                        className="btn-secondary"
                        style={{ marginTop: '6px', padding: '4px 8px', fontSize: '11px' }}
                      >
                        Change Image
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Decoded Backend Preview Summary */}
              {decodedData?.success && (
                <div style={{
                  padding: '12px 14px',
                  backgroundColor: '#F0FDF4',
                  border: '1px solid #BBF7D0',
                  borderRadius: '10px',
                  fontSize: '12px',
                }}>
                  <div style={{ fontWeight: 700, color: '#166534', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check_circle</span>
                    Decoded UPI Parameters from Image:
                  </div>
                  <div style={{ color: '#15803D' }}>
                    Destination: <strong>{decodedData.extracted_fields?.expected_upi_id || 'N/A'}</strong> • 
                    Payee: <strong>{decodedData.extracted_fields?.official_recipient_name || 'N/A'}</strong>
                    {decodedData.extracted_fields?.expected_amount && (
                      <> • Amount: <strong>₹{decodedData.extracted_fields.expected_amount}</strong></>
                    )}
                  </div>
                </div>
              )}

              {/* Duplicate Warnings */}
              {duplicateWarnings.length > 0 && (
                <div style={{
                  padding: '12px 14px',
                  backgroundColor: '#FFFBEB',
                  border: '1px solid #FDE68A',
                  borderRadius: '10px',
                  fontSize: '12px',
                  color: '#92400E',
                }}>
                  <strong>Duplicate Warnings Detected:</strong>
                  <ul style={{ margin: '4px 0 0 16px' }}>
                    {duplicateWarnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                </div>
              )}

              {/* Form Input Fields */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Display Name / Counter Name *
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Accounts Office Tuition Fee Counter"
                    required
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Payment Purpose *
                  </label>
                  <select
                    value={paymentPurpose}
                    onChange={(e) => setPaymentPurpose(e.target.value)}
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  >
                    {purposesList.map((p, idx) => (
                      <option key={idx} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Official Recipient / Merchant Name *
                  </label>
                  <input
                    type="text"
                    value={officialRecipient}
                    onChange={(e) => setOfficialRecipient(e.target.value)}
                    placeholder="e.g. Jain College of Engineering & Research"
                    required
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Expected Destination UPI ID *
                  </label>
                  <input
                    type="text"
                    value={expectedUpiId}
                    onChange={(e) => setExpectedUpiId(e.target.value)}
                    placeholder="e.g. jaincollege9120@fbl"
                    required
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Department / College Unit
                  </label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  >
                    {departmentsList.map((d, idx) => (
                      <option key={idx} value={d}>{d}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Expected Amount (₹ Optional)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={expectedAmount}
                    onChange={(e) => setExpectedAmount(e.target.value)}
                    placeholder="Leave blank for variable amount"
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Description / Location Notes
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="e.g. Counter #2 at Administrative Block Ground Floor. Standee updated for 2026."
                  rows={2}
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                />
              </div>

              {/* Approval Option */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="autoApprove"
                  checked={autoApprove}
                  onChange={(e) => setAutoApprove(e.target.checked)}
                />
                <label htmlFor="autoApprove" style={{ fontSize: '13px', color: '#374151', cursor: 'pointer' }}>
                  <strong>Approve and activate immediately</strong> (Available to QR Scanner right away)
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="btn-secondary"
                  disabled={isSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isSubmitting || !singleFile}
                >
                  {isSubmitting ? 'Registering in PostgreSQL...' : 'Register QR Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 2: Bulk Upload QR Code Images                       */}
      {/* ========================================================= */}
      {showBulkModal && (
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
            maxWidth: '580px',
            width: '100%',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px', color: '#7138E8' }}>
                  upload
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
                  Bulk Upload College Payment QRs
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowBulkModal(false)}
                className="btn-secondary"
                style={{ padding: '4px 8px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>close</span>
              </button>
            </div>

            <form onSubmit={handleBulkUploadSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: '#374151', marginBottom: '6px' }}>
                  Select Multiple QR Code Images *
                </label>
                <input
                  ref={bulkFileInputRef}
                  type="file"
                  multiple
                  accept="image/png,image/jpeg,image/jpg,image/webp"
                  onChange={(e) => setBulkFiles(Array.from(e.target.files || []))}
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                />
                <div style={{ fontSize: '11.5px', color: '#6B7280', marginTop: '4px' }}>
                  {bulkFiles.length} file(s) selected. Each file will be individually decoded and registered.
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Default Payment Purpose
                  </label>
                  <select
                    value={bulkPurpose}
                    onChange={(e) => setBulkPurpose(e.target.value)}
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  >
                    {purposesList.map((p, idx) => (
                      <option key={idx} value={p}>{p}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Default Department
                  </label>
                  <select
                    value={bulkDepartment}
                    onChange={(e) => setBulkDepartment(e.target.value)}
                    className="input-field"
                    style={{ width: '100%', fontSize: '13px' }}
                  >
                    {departmentsList.map((d, idx) => (
                      <option key={idx} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <input
                  type="checkbox"
                  id="bulkAutoApprove"
                  checked={bulkAutoApprove}
                  onChange={(e) => setBulkAutoApprove(e.target.checked)}
                />
                <label htmlFor="bulkAutoApprove" style={{ fontSize: '13px', color: '#374151', cursor: 'pointer' }}>
                  Activate immediately after successful decoding
                </label>
              </div>

              {/* Bulk Results Feedback */}
              {bulkResult && (
                <div style={{ padding: '10px 14px', borderRadius: '8px', backgroundColor: '#F8F9FD', border: '1px solid #E5EAF1', fontSize: '12.5px' }}>
                  <div style={{ fontWeight: 700, color: '#202124', marginBottom: '4px' }}>
                    Bulk Import Results: {bulkResult.successful_count} Success, {bulkResult.failed_count} Failed
                  </div>
                  {bulkResult.failed && bulkResult.failed.length > 0 && (
                    <div style={{ color: '#DC2626', marginTop: '6px' }}>
                      <strong>Failed Files:</strong>
                      <ul style={{ margin: '4px 0 0 16px' }}>
                        {bulkResult.failed.map((f, i) => (
                          <li key={i}>{f.filename}: {f.reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px' }}>
                <button
                  type="button"
                  onClick={() => setShowBulkModal(false)}
                  className="btn-secondary"
                  disabled={isBulkSubmitting}
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isBulkSubmitting || bulkFiles.length === 0}
                >
                  {isBulkSubmitting ? 'Processing Batch...' : `Import ${bulkFiles.length} QR Image(s)`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 3: Inspect Record Details                           */}
      {/* ========================================================= */}
      {inspectRecord && (
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
            maxWidth: '560px',
            width: '100%',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '24px', color: '#7138E8' }}>
                  qr_code_2
                </span>
                <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
                  {inspectRecord.display_name}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setInspectRecord(null)}
                className="btn-secondary"
                style={{ padding: '4px 8px' }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>close</span>
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '13px' }}>
              <div><strong>Record ID:</strong> <code>{inspectRecord.record_id}</code></div>
              <div><strong>Payment Purpose:</strong> {inspectRecord.payment_purpose}</div>
              <div><strong>Department:</strong> {inspectRecord.department || 'General Administration'}</div>
              <div><strong>Official Recipient:</strong> {inspectRecord.official_recipient_name}</div>
              <div><strong>Expected UPI ID:</strong> <code>{inspectRecord.expected_upi_id}</code></div>
              <div>
                <strong>Amount:</strong> {inspectRecord.expected_amount ? `₹${inspectRecord.expected_amount.toFixed(2)}` : 'Variable Amount'}
              </div>
              <div>
                <strong>Status:</strong> {inspectRecord.is_active ? 'Active & Approved' : inspectRecord.approval_status}
              </div>
              <div>
                <strong>Decoded Raw Payload:</strong>
                <pre style={{
                  backgroundColor: '#F8F9FD',
                  padding: '8px 10px',
                  borderRadius: '6px',
                  fontSize: '11.5px',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-all',
                  marginTop: '4px',
                  border: '1px solid #E5EAF1',
                }}>
                  {inspectRecord.qr_payload}
                </pre>
              </div>
              <div>
                <strong>Canonical Fingerprint (SHA-256):</strong>
                <code style={{ fontSize: '11px', wordBreak: 'break-all', display: 'block', marginTop: '2px' }}>
                  {inspectRecord.payload_fingerprint}
                </code>
              </div>
              {inspectRecord.description && (
                <div><strong>Description:</strong> {inspectRecord.description}</div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button
                type="button"
                onClick={() => setInspectRecord(null)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 4: Edit Metadata                                    */}
      {/* ========================================================= */}
      {editRecord && (
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
            maxWidth: '540px',
            width: '100%',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124', marginBottom: '14px' }}>
              Edit QR Record: {editRecord.record_id}
            </h3>

            <form onSubmit={handleEditSave} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Display Name
                </label>
                <input
                  type="text"
                  value={editRecord.display_name}
                  onChange={(e) => setEditRecord({ ...editRecord, display_name: e.target.value })}
                  required
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Payment Purpose
                </label>
                <select
                  value={editRecord.payment_purpose}
                  onChange={(e) => setEditRecord({ ...editRecord, payment_purpose: e.target.value })}
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                >
                  {purposesList.map((p, idx) => (
                    <option key={idx} value={p}>{p}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Department
                </label>
                <select
                  value={editRecord.department || ''}
                  onChange={(e) => setEditRecord({ ...editRecord, department: e.target.value })}
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                >
                  {departmentsList.map((d, idx) => (
                    <option key={idx} value={d}>{d}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Official Recipient Name
                </label>
                <input
                  type="text"
                  value={editRecord.official_recipient_name}
                  onChange={(e) => setEditRecord({ ...editRecord, official_recipient_name: e.target.value })}
                  required
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Expected Amount (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={editRecord.expected_amount || ''}
                  onChange={(e) => setEditRecord({ ...editRecord, expected_amount: e.target.value ? parseFloat(e.target.value) : null })}
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12.5px', fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                  Description Notes
                </label>
                <textarea
                  value={editRecord.description || ''}
                  onChange={(e) => setEditRecord({ ...editRecord, description: e.target.value })}
                  rows={2}
                  className="input-field"
                  style={{ width: '100%', fontSize: '13px' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setEditRecord(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 5: Replace QR Image                                 */}
      {/* ========================================================= */}
      {replaceRecord && (
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
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124', marginBottom: '10px' }}>
              Replace QR Image for '{replaceRecord.display_name}'
            </h3>
            <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '16px' }}>
              Select a new QR image to replace the existing standee. The backend will re-decode the payload and update the fingerprint.
            </p>

            <input
              ref={replaceFileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/jpg,image/webp"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleReplaceImage(file);
              }}
              style={{ display: 'none' }}
            />

            <button
              type="button"
              onClick={() => replaceFileInputRef.current?.click()}
              className="btn-primary"
              style={{ width: '100%', padding: '12px', justifyContent: 'center' }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: '20px' }}>upload_file</span>
              <span>Select New QR Image</span>
            </button>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
              <button
                type="button"
                onClick={() => setReplaceRecord(null)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* MODAL 6: Archive Confirmation                             */}
      {/* ========================================================= */}
      {archiveTarget && (
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
            maxWidth: '460px',
            width: '100%',
            padding: '24px',
            boxShadow: 'var(--shadow-modal)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#DC2626', marginBottom: '12px' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>archive</span>
              <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#202124' }}>
                Archive College QR Record?
              </h3>
            </div>

            <p style={{ fontSize: '13.5px', color: '#4B5563', lineHeight: '1.5', marginBottom: '16px' }}>
              Are you sure you want to archive <strong>'{archiveTarget.display_name}' ({archiveTarget.record_id})</strong>? 
              This will deactivate the record from active QR verification. Historical scan logs will remain preserved.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setArchiveTarget(null)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleArchiveConfirm}
                className="btn-danger"
              >
                Confirm & Archive
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

