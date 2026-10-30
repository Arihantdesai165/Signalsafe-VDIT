import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';

export default function IncidentReports() {
  const [incidents, setIncidents] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selected incident for detail modal
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [newNoteText, setNewNoteText] = useState('');
  const [statusActionNote, setStatusActionNote] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [modalFeedback, setModalFeedback] = useState(null);

  const fetchIncidents = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listIncidents({
        search: searchTerm,
        status: statusFilter,
        category: categoryFilter,
        page,
        pageSize,
      });
      setIncidents(data.incidents || []);
      setTotal(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to load incident reports:', err);
      setError(err.message || 'Failed to load incident reports from server.');
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, statusFilter, categoryFilter, page, pageSize]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  // Open modal and fetch freshest details
  const handleOpenDetail = async (incident) => {
    setSelectedIncident(incident);
    setNewNoteText('');
    setStatusActionNote('');
    setModalFeedback(null);
    try {
      const fresh = await api.getIncident(incident.id);
      setSelectedIncident(fresh);
    } catch (err) {
      console.warn('Could not fetch refreshed detail:', err);
    }
  };

  // Status transition handler
  const handleUpdateStatus = async (targetStatus) => {
    if (!selectedIncident) return;
    setIsUpdatingStatus(true);
    setModalFeedback(null);
    try {
      const updated = await api.updateIncidentStatus(
        selectedIncident.id,
        targetStatus,
        statusActionNote.trim() || undefined
      );
      setSelectedIncident(updated);
      setStatusActionNote('');
      setModalFeedback({ type: 'success', text: `Status successfully updated to ${targetStatus}.` });
      // Refresh background table list
      fetchIncidents();
    } catch (err) {
      setModalFeedback({ type: 'error', text: err.message || 'Status update failed.' });
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  // Add investigation note
  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNoteText.trim() || !selectedIncident) return;
    setIsAddingNote(true);
    setModalFeedback(null);
    try {
      const updated = await api.addIncidentNote(selectedIncident.id, newNoteText.trim());
      setSelectedIncident(updated);
      setNewNoteText('');
      setModalFeedback({ type: 'success', text: 'Investigation note appended successfully.' });
      fetchIncidents();
    } catch (err) {
      setModalFeedback({ type: 'error', text: err.message || 'Failed to add note.' });
    } finally {
      setIsAddingNote(false);
    }
  };

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* 5.1 Page Header */}
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
              fontSize: '24px',
              fontWeight: 800,
              color: '#202124',
              letterSpacing: '-0.02em',
            }}>
              Incident Reports
            </h1>
            <span style={{
              fontSize: '11px',
              fontWeight: 700,
              padding: '3px 9px',
              borderRadius: 'var(--radius-full)',
              backgroundColor: '#F3E8FF',
              color: '#7138E8',
              border: '1px solid #DDD6FE',
            }}>
              {total} TOTAL REPORTS
            </span>
          </div>
          <p style={{
            fontSize: '13.5px',
            color: '#6B7280',
            marginTop: '4px',
          }}>
            Review, investigate, and track cybersecurity incidents reported across the campus.
          </p>
        </div>

        {/* Refresh Action */}
        <button
          onClick={fetchIncidents}
          disabled={isLoading}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <span className={`material-symbols-outlined ${isLoading ? 'spin-icon' : ''}`} style={{ fontSize: '18px' }}>
            refresh
          </span>
          <span>Refresh Queue</span>
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

      {/* Search & Filter Toolbar (Inspired by reference screenshot) */}
      <div style={{
        backgroundColor: '#FFFFFF',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-lg)',
        padding: '16px 20px',
        boxShadow: 'var(--shadow-card)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '14px',
      }}>
        {/* Search Input */}
        <div style={{ position: 'relative', flex: '1 1 300px', minWidth: '240px' }}>
          <span className="material-symbols-outlined" style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: '#9CA3AF',
            fontSize: '18px',
          }}>
            search
          </span>
          <input
            type="text"
            className="erp-input"
            style={{ paddingLeft: '38px', height: '40px' }}
            placeholder="Search by report ID, reporter, description, evidence..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
          />
        </div>

        {/* Dropdowns */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Category Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Category
            </span>
            <select
              className="erp-select"
              value={categoryFilter}
              onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            >
              <option value="ALL">All Categories</option>
              <option value="phishing_url">Phishing URL</option>
              <option value="upi_qr_scam">Fraudulent QR Code</option>
              <option value="fake_payment_screenshot">Fake Screenshot</option>
              <option value="suspicious_sms">Scam SMS / Smishing</option>
              <option value="credential_theft">Credential Theft</option>
              <option value="other">Other Threats</option>
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: '#6B7280', textTransform: 'uppercase' }}>
              Status
            </span>
            <select
              className="erp-select"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            >
              <option value="ALL">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="Under Review">Under Review</option>
              <option value="Resolved">Resolved</option>
              <option value="Rejected">Rejected</option>
            </select>
          </div>
        </div>
      </div>

      {/* Incident Table (Exact dark header matching reference screenshot) */}
      <div className="erp-table-container">
        <table className="erp-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check_box_outline_blank</span>
              </th>
              <th>REPORT ID</th>
              <th>REPORTER INFO</th>
              <th>CATEGORY</th>
              <th>EVIDENCE / TARGET</th>
              <th>DATE REPORTED</th>
              <th>STATUS</th>
              <th style={{ textAlign: 'right' }}>ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '48px 20px', color: '#6B7280' }}>
                  <span className="material-symbols-outlined spin-icon" style={{ fontSize: '24px', color: '#7138E8' }}>
                    sync
                  </span>
                  <div style={{ marginTop: '8px', fontSize: '13px', fontWeight: 500 }}>
                    Loading incident queue from server...
                  </div>
                </td>
              </tr>
            ) : incidents.length === 0 ? (
              <tr>
                <td colSpan="8" className="erp-table-empty">
                  NO INCIDENTS IN THIS STAGE PIPELINE.
                </td>
              </tr>
            ) : (
              incidents.map((inc) => (
                <tr key={inc.id} onClick={() => handleOpenDetail(inc)} style={{ cursor: 'pointer' }}>
                  <td onClick={(e) => e.stopPropagation()}>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px', color: '#9CA3AF' }}>
                      check_box_outline_blank
                    </span>
                  </td>
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
                      padding: '3px 8px',
                      borderRadius: '4px',
                      backgroundColor: '#F3F4F6',
                      color: '#374151',
                    }}>
                      {inc.category_label || inc.category}
                    </span>
                  </td>
                  <td style={{ maxWidth: '240px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    <code style={{
                      fontSize: '11.5px',
                      backgroundColor: '#F3F4F6',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      color: '#1E293B',
                    }}>
                      {inc.target_evidence}
                    </code>
                  </td>
                  <td style={{ fontSize: '12px', color: '#6B7280' }}>
                    {new Date(inc.created_at).toLocaleDateString()}
                  </td>
                  <td>
                    <span className={`status-pill ${getStatusClass(inc.status)}`}>
                      {inc.status}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => handleOpenDetail(inc)}
                      className="btn-outline"
                    >
                      <span>Investigate</span>
                      <span className="material-symbols-outlined" style={{ fontSize: '14px' }}>visibility</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination Bar */}
        <div style={{
          padding: '14px 20px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '12.5px',
          color: '#6B7280',
        }}>
          <div>
            Showing Page <strong style={{ color: '#202124' }}>{page}</strong> of <strong style={{ color: '#202124' }}>{totalPages}</strong> ({total} total incidents)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1}
              className="btn-secondary"
              style={{ padding: '5px 12px', fontSize: '12px' }}
            >
              Previous
            </button>
            <button
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages}
              className="btn-secondary"
              style={{ padding: '5px 12px', fontSize: '12px' }}
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* 5.2 Report Details Modal */}
      {selectedIncident && (
        <div className="modal-overlay" onClick={() => setSelectedIncident(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div style={{
              padding: '20px 24px',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: 800, color: '#202124' }}>
                    Incident {selectedIncident.id}
                  </h3>
                  <span className={`status-pill ${getStatusClass(selectedIncident.status)}`}>
                    {selectedIncident.status}
                  </span>
                  <span style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: selectedIncident.severity === 'Critical' ? '#FEF2F2' : '#FFFBEB',
                    color: selectedIncident.severity === 'Critical' ? '#DC2626' : '#D97706',
                    border: `1px solid ${selectedIncident.severity === 'Critical' ? '#FECACA' : '#FDE68A'}`,
                  }}>
                    {selectedIncident.severity || 'Medium'} Severity
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#6B7280', marginTop: '3px' }}>
                  Reported on {new Date(selectedIncident.created_at).toLocaleString()}
                </div>
              </div>

              <button
                onClick={() => setSelectedIncident(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6B7280',
                  cursor: 'pointer',
                  padding: '6px',
                }}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '22px' }}>close</span>
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {modalFeedback && (
                <div style={{
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12.5px',
                  backgroundColor: modalFeedback.type === 'success' ? '#F0FDF4' : '#FEF2F2',
                  color: modalFeedback.type === 'success' ? '#16A34A' : '#DC2626',
                  border: `1px solid ${modalFeedback.type === 'success' ? '#BBF7D0' : '#FECACA'}`,
                }}>
                  {modalFeedback.text}
                </div>
              )}

              {/* Reporter Metadata Grid */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
                backgroundColor: '#F9FAFD',
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
              }}>
                <div>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280' }}>Reported By</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#202124' }}>
                    {selectedIncident.reported_by}
                  </div>
                  <div style={{ fontSize: '11px', color: '#6B7280' }}>{selectedIncident.reporter_email}</div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280' }}>Role & Department</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#202124' }}>
                    {selectedIncident.reporter_role}
                  </div>
                  <div style={{ fontSize: '11px', color: '#6B7280' }}>
                    {selectedIncident.reporter_dept || 'Campus'}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', fontWeight: 600, color: '#6B7280' }}>Incident Category</div>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#202124' }}>
                    {selectedIncident.category_label || selectedIncident.category}
                  </div>
                </div>
              </div>

              {/* Target / Evidence Box (Escaped raw text, never auto-navigated) */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase' }}>
                  Target / Submitted Evidence
                </label>
                <div style={{
                  marginTop: '6px',
                  padding: '12px 14px',
                  backgroundColor: '#F1F5F9',
                  border: '1px solid #E2E8F0',
                  borderRadius: 'var(--radius-sm)',
                  fontFamily: 'monospace',
                  fontSize: '12.5px',
                  color: '#0F172A',
                  wordBreak: 'break-all',
                  userSelect: 'all',
                }}>
                  {selectedIncident.target_evidence}
                </div>
                <div style={{ fontSize: '11px', color: '#64748B', marginTop: '4px' }}>
                  Target evidence is treated as untrusted text. Do not visit suspicious links directly.
                </div>
              </div>

              {/* Description */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase' }}>
                  Incident Description
                </label>
                <div style={{
                  marginTop: '6px',
                  padding: '12px 14px',
                  backgroundColor: '#FFFFFF',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '13px',
                  color: '#202124',
                  lineHeight: 1.5,
                }}>
                  {selectedIncident.description}
                </div>
              </div>

              {/* 5.3 Workflow Status Change Actions */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase' }}>
                  Change Incident Status
                </label>
                <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  <button
                    onClick={() => handleUpdateStatus('Under Review')}
                    disabled={isUpdatingStatus || selectedIncident.status === 'Under Review'}
                    className="btn-secondary"
                    style={{
                      backgroundColor: selectedIncident.status === 'Under Review' ? '#F3E8FF' : '#FFFFFF',
                      borderColor: '#DDD6FE',
                      color: '#7138E8',
                      fontWeight: 600,
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>search</span>
                    <span>Move to Under Review</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus('Resolved')}
                    disabled={isUpdatingStatus || selectedIncident.status === 'Resolved'}
                    className="btn-secondary"
                    style={{
                      backgroundColor: selectedIncident.status === 'Resolved' ? '#F0FDF4' : '#FFFFFF',
                      borderColor: '#BBF7D0',
                      color: '#16A34A',
                      fontWeight: 600,
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>check_circle</span>
                    <span>Mark Resolved</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus('Rejected')}
                    disabled={isUpdatingStatus || selectedIncident.status === 'Rejected'}
                    className="btn-secondary"
                    style={{
                      backgroundColor: selectedIncident.status === 'Rejected' ? '#FEF2F2' : '#FFFFFF',
                      borderColor: '#FECACA',
                      color: '#DC2626',
                      fontWeight: 600,
                    }}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>cancel</span>
                    <span>Reject / Invalid</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus('Pending')}
                    disabled={isUpdatingStatus || selectedIncident.status === 'Pending'}
                    className="btn-secondary"
                    style={{
                      borderColor: '#FDE68A',
                      color: '#D97706',
                      fontWeight: 600,
                    }}
                  >
                    <span>Reset to Pending</span>
                  </button>
                </div>

                <div style={{ marginTop: '8px' }}>
                  <input
                    type="text"
                    className="erp-input"
                    placeholder="Optional note explaining this status transition..."
                    value={statusActionNote}
                    onChange={(e) => setStatusActionNote(e.target.value)}
                    style={{ fontSize: '12.5px', height: '36px' }}
                  />
                </div>
              </div>

              {/* Investigation Notes History */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase' }}>
                  Investigation Notes ({selectedIncident.notes?.length || 0})
                </label>
                <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(!selectedIncident.notes || selectedIncident.notes.length === 0) ? (
                    <div style={{ fontSize: '12px', color: '#6B7280', fontStyle: 'italic', padding: '6px 0' }}>
                      No investigation notes recorded yet.
                    </div>
                  ) : (
                    selectedIncident.notes.map((note) => (
                      <div key={note.id} style={{
                        padding: '10px 12px',
                        backgroundColor: '#F9FAFB',
                        border: '1px solid var(--border-color)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '12.5px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span style={{ fontWeight: 600, color: '#7138E8' }}>{note.author} ({note.role})</span>
                          <span style={{ fontSize: '11px', color: '#6B7280' }}>
                            {new Date(note.timestamp).toLocaleString()}
                          </span>
                        </div>
                        <div style={{ color: '#202124' }}>{note.text}</div>
                      </div>
                    ))
                  )}
                </div>

                {/* Add Note Form */}
                <form onSubmit={handleAddNote} style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    className="erp-input"
                    placeholder="Write an investigation note or mitigation step..."
                    value={newNoteText}
                    onChange={(e) => setNewNoteText(e.target.value)}
                    style={{ fontSize: '12.5px' }}
                  />
                  <button
                    type="submit"
                    disabled={isAddingNote || !newNoteText.trim()}
                    className="btn-primary"
                    style={{ padding: '8px 16px', fontSize: '12.5px', whiteSpace: 'nowrap' }}
                  >
                    <span>Add Note</span>
                  </button>
                </form>
              </div>

              {/* Chronological Audit Trail */}
              <div>
                <label style={{ fontSize: '12px', fontWeight: 700, color: '#374151', textTransform: 'uppercase' }}>
                  Audit Trail
                </label>
                <div style={{
                  marginTop: '8px',
                  backgroundColor: '#FFFFFF',
                  border: '1px solid var(--border-color)',
                  borderRadius: 'var(--radius-sm)',
                  maxHeight: '160px',
                  overflowY: 'auto',
                }}>
                  {selectedIncident.audit_trail?.map((entry, idx) => (
                    <div key={idx} style={{
                      padding: '8px 12px',
                      borderBottom: idx === selectedIncident.audit_trail.length - 1 ? 'none' : '1px solid var(--border-color)',
                      fontSize: '11.5px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '8px',
                    }}>
                      <div>
                        <strong style={{ color: '#202124' }}>{entry.action}</strong>
                        <span style={{ color: '#6B7280', marginLeft: '6px' }}>by {entry.by}</span>
                        {entry.note && (
                          <div style={{ color: '#4B5563', fontSize: '11px', marginTop: '1px' }}>
                            "{entry.note}"
                          </div>
                        )}
                      </div>
                      <span style={{ color: '#9CA3AF', whiteSpace: 'nowrap', fontSize: '10.5px' }}>
                        {new Date(entry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '16px 24px',
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'flex-end',
            }}>
              <button
                onClick={() => setSelectedIncident(null)}
                className="btn-secondary"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
