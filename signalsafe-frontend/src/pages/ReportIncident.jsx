import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

export default function ReportIncident() {
  const navigate = useNavigate();
  const [category, setCategory] = useState('phishing_url');
  const [targetEvidence, setTargetEvidence] = useState('');
  const [description, setDescription] = useState('');
  const [severity, setSeverity] = useState('High');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!targetEvidence.trim()) {
      setErrorMessage('Please provide the target evidence (URL, UPI ID, or phone number).');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setSubmissionResult(null);

    try {
      const payload = {
        category,
        target_evidence: targetEvidence.trim(),
        description: description.trim(),
        severity,
      };

      const result = await api.createIncident(payload);
      setSubmissionResult(result);
    } catch (err) {
      console.error('Incident report error:', err);
      setErrorMessage(err.message || 'Failed to submit incident report. Please check your connection.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setCategory('phishing_url');
    setTargetEvidence('');
    setDescription('');
    setSeverity('High');
    setSubmissionResult(null);
    setErrorMessage(null);
  };

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
            <span className="material-symbols-outlined" style={{ fontSize: '24px' }}>flag</span>
          </div>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
              Report a Security Incident
            </h1>
            <p style={{ fontSize: '13.5px', color: '#6B7280' }}>
              Report suspected phishing, fraudulent websites, suspicious links, QR-code scams, or other cyber incidents.
            </p>
          </div>
        </div>
      </div>

      {/* Main Form Card */}
      <div className="erp-card">
        {submissionResult ? (
          <div style={{ textAlign: 'center', padding: '32px 16px' }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              backgroundColor: '#F0FDF4',
              border: '2px solid #BBF7D0',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#16A34A',
              marginBottom: '16px',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '32px' }}>check_circle</span>
            </div>

            <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#202124' }}>
              Incident Report Submitted Successfully
            </h2>
            <p style={{ fontSize: '14px', color: '#6B7280', marginTop: '6px', maxWidth: '520px', margin: '6px auto 0' }}>
              Your report has been logged and assigned to the campus CyberAdmin review queue.
            </p>

            <div style={{
              margin: '24px auto',
              maxWidth: '420px',
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: '#F9FAFB',
              border: '1px solid var(--border-color)',
              textAlign: 'left',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', color: '#6B7280' }}>Tracking ID:</span>
                <strong style={{ fontSize: '13px', color: '#7138E8' }}>{submissionResult.id}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', color: '#6B7280' }}>Initial Status:</span>
                <span className="status-pill status-pending">{submissionResult.status}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', color: '#6B7280' }}>Reported By:</span>
                <span style={{ fontSize: '12px', fontWeight: 600 }}>{submissionResult.reported_by}</span>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', marginTop: '20px' }}>
              <button onClick={handleReset} className="btn-secondary">
                Submit Another Report
              </button>
              <button onClick={() => navigate('/dashboard')} className="btn-primary">
                Return to Dashboard
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {errorMessage && (
              <div style={{
                padding: '12px 16px',
                backgroundColor: '#FEF2F2',
                border: '1px solid #FECACA',
                borderRadius: 'var(--radius-md)',
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

            {/* Incident Category */}
            <div>
              <label style={{ fontSize: '13px', fontWeight: 700, color: '#374151', display: 'block', marginBottom: '6px' }}>
                Incident Category *
              </label>
              <select
                className="erp-select"
                style={{ width: '100%', height: '42px' }}
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="phishing_url">Phishing URL / Fake College Webpage</option>
                <option value="upi_qr_scam">Counterfeit UPI QR Code / Standee Tampering</option>
                <option value="fake_payment_screenshot">Fake Payment Confirmation Screenshot</option>
                <option value="suspicious_sms">Fraudulent SMS / Smishing Scam</option>
                <option value="credential_theft">Credential Harvesting / Account Impersonation</option>
                <option value="other">Other Cyber Threat</option>
              </select>
            </div>

            {/* Target Evidence */}
            <div>
              <label style={{ fontSize: '13px', fontWeight: 700, color: '#374151', display: 'block', marginBottom: '6px' }}>
                Target / Evidence (URL, UPI ID, Phone Number, or Identifier) *
              </label>
              <input
                type="text"
                className="erp-input"
                placeholder="e.g. http://paytem-fake-login.xyz or upi://pay?pa=scam@bank"
                value={targetEvidence}
                onChange={(e) => setTargetEvidence(e.target.value)}
                required
              />
              <span style={{ fontSize: '11.5px', color: '#6B7280', marginTop: '4px', display: 'block' }}>
                Paste the exact link, UPI ID, or phone header received.
              </span>
            </div>

            {/* Severity Level */}
            <div>
              <label style={{ fontSize: '13px', fontWeight: 700, color: '#374151', display: 'block', marginBottom: '6px' }}>
                Estimated Severity
              </label>
              <select
                className="erp-select"
                style={{ width: '100%', height: '42px' }}
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
              >
                <option value="Low">Low – Informational / Minor</option>
                <option value="Medium">Medium – Suspicious message without financial loss</option>
                <option value="High">High – Active scam link / fake fee payment portal</option>
                <option value="Critical">Critical – Compromised credentials / active campus-wide fraud</option>
              </select>
            </div>

            {/* Description */}
            <div>
              <label style={{ fontSize: '13px', fontWeight: 700, color: '#374151', display: 'block', marginBottom: '6px' }}>
                Incident Description & Context
              </label>
              <textarea
                className="erp-input"
                rows="4"
                placeholder="Describe how you encountered this threat, what was requested, and any additional details..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={{ resize: 'vertical' }}
              />
            </div>

            {/* Submit Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="btn-secondary"
                disabled={isSubmitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn-primary"
                disabled={isSubmitting || !targetEvidence.trim()}
              >
                {isSubmitting ? (
                  <>
                    <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>sync</span>
                    <span>Submitting Report...</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>send</span>
                    <span>Submit Incident Report</span>
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
