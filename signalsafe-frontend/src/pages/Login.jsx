import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    isAuthenticated,
    user,
    login,
    verifyDailyOtp,
    resendDailyOtp,
    requiresDailyOtp,
    pendingOtpEmail,
    cancelOtpChallenge,
    authError,
    setAuthError,
  } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  // If already authenticated, redirect to appropriate role dashboard
  useEffect(() => {
    if (isAuthenticated) {
      const isCyberAdmin = (user?.role || '').toUpperCase() === 'CYBERADMIN';
      const target = location.state?.from?.pathname || (isCyberAdmin ? '/dashboard' : '/dashboard');
      navigate(target, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location]);

  // Resend OTP countdown timer
  useEffect(() => {
    let timer;
    if (resendCooldown > 0) {
      timer = setInterval(() => {
        setResendCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleCredentialsSubmit = async (e) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setAuthError('Please enter both your User ID / USN / Email and ERP Password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await login(email, password);
      if (res?.requiresDailyOtp) {
        setResendCooldown(60);
      } else if (res?.success) {
        const isCyberAdmin = (res.user?.role || '').toUpperCase() === 'CYBERADMIN';
        const target = location.state?.from?.pathname || (isCyberAdmin ? '/dashboard' : '/dashboard');
        navigate(target, { replace: true });
      }
    } catch (err) {
      console.warn('Login failure:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    if (!otp.trim() || otp.trim().length !== 6) {
      setAuthError('Please enter a valid 6-digit verification code.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await verifyDailyOtp(otp);
      if (res?.success) {
        const isCyberAdmin = (res.user?.role || '').toUpperCase() === 'CYBERADMIN';
        const target = location.state?.from?.pathname || (isCyberAdmin ? '/dashboard' : '/dashboard');
        navigate(target, { replace: true });
      }
    } catch (err) {
      console.warn('OTP failure:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    try {
      await resendDailyOtp();
      setResendCooldown(60);
    } catch (err) {
      console.warn('Resend error:', err);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      backgroundColor: '#F5F5FB',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '430px',
        backgroundColor: '#FFFFFF',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-xl)',
        padding: '36px 32px',
        boxShadow: 'var(--shadow-modal)',
      }}>
        {/* Portal Branding matching ERP screenshot */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          {/* Circular JGI Seal */}
          <div style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: '#1E3A8A',
            background: 'linear-gradient(135deg, #1E3A8A 0%, #172554 100%)',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '18px',
            letterSpacing: '0.05em',
            boxShadow: '0 4px 14px rgba(30, 58, 138, 0.25)',
            border: '2px solid #DBEAFE',
            marginBottom: '14px',
          }}>
            JGI
          </div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#202124', letterSpacing: '-0.02em' }}>
            SignalSafe Campus
          </h1>
          <p style={{ fontSize: '13px', color: '#6B7280', marginTop: '4px' }}>
            JCER ERP Authentication • Campus Cybersecurity
          </p>
          <div style={{
            display: 'inline-block',
            marginTop: '8px',
            padding: '3px 10px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: '#F3E8FF',
            color: '#7138E8',
            fontSize: '11px',
            fontWeight: 700,
            border: '1px solid #DDD6FE',
          }}>
            CyberAdmin & Student Security Portal
          </div>
        </div>

        {/* Error Alert */}
        {authError && (
          <div style={{
            padding: '12px 14px',
            backgroundColor: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: 'var(--radius-md)',
            color: '#DC2626',
            fontSize: '12.5px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '8px',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: '18px', marginTop: '1px', flexShrink: 0 }}>
              error
            </span>
            <span>{authError}</span>
          </div>
        )}

        {/* STEP 1: ERP Credentials Login */}
        {!requiresDailyOtp ? (
          <form onSubmit={handleCredentialsSubmit}>
            <div style={{ marginBottom: '18px' }}>
              <label style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 700,
                color: '#4B5563',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '6px',
              }}>
                User ID / USN / Email
              </label>
              <input
                type="text"
                className="erp-input"
                placeholder="e.g. cyberadmin@jcer.edu.in or USN"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
              />
            </div>

            <div style={{ marginBottom: '22px' }}>
              <label style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 700,
                color: '#4B5563',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '6px',
              }}>
                ERP Password
              </label>
              <div style={{ position: 'relative' }}>
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="erp-input"
                  placeholder="Enter your JCER ERP account password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  style={{ paddingRight: '40px' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    background: 'none',
                    border: 'none',
                    color: '#6B7280',
                    cursor: 'pointer',
                    padding: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
              style={{ width: '100%', padding: '12px', fontSize: '14px', borderRadius: 'var(--radius-md)' }}
            >
              {isSubmitting ? (
                <>
                  <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>
                    sync
                  </span>
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                    lock_open
                  </span>
                  <span>Sign In Securely</span>
                </>
              )}
            </button>
          </form>
        ) : (
          /* STEP 2: Staff / Admin Daily OTP Verification Challenge */
          <form onSubmit={handleOtpSubmit}>
            <div style={{
              padding: '14px',
              backgroundColor: '#F3E8FF',
              border: '1px solid #DDD6FE',
              borderRadius: 'var(--radius-md)',
              marginBottom: '20px',
              textAlign: 'center',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: '28px', color: '#7138E8', marginBottom: '6px' }}>
                mark_email_read
              </span>
              <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#6B21A8' }}>
                Daily 2FA OTP Challenge
              </div>
              <div style={{ fontSize: '12px', color: '#7E22CE', marginTop: '4px' }}>
                Enter the 6-digit security code issued for <strong>{pendingOtpEmail}</strong>
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                fontSize: '11.5px',
                fontWeight: 700,
                color: '#4B5563',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '6px',
                textAlign: 'center',
              }}>
                6-Digit Verification Code
              </label>
              <input
                type="text"
                className="erp-input"
                placeholder="• • • • • •"
                maxLength={6}
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                autoFocus
                required
                style={{
                  textAlign: 'center',
                  fontSize: '22px',
                  fontWeight: 800,
                  letterSpacing: '0.3em',
                  height: '48px',
                }}
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting || otp.length !== 6}
              style={{ width: '100%', padding: '12px', fontSize: '14px', borderRadius: 'var(--radius-md)' }}
            >
              {isSubmitting ? (
                <>
                  <span className="material-symbols-outlined spin-icon" style={{ fontSize: '18px' }}>
                    sync
                  </span>
                  <span>Validating OTP...</span>
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>
                    verified_user
                  </span>
                  <span>Verify & Access Portal</span>
                </>
              )}
            </button>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '16px',
              fontSize: '12px',
            }}>
              <button
                type="button"
                onClick={cancelOtpChallenge}
                className="btn-secondary"
                style={{ padding: '4px 10px', fontSize: '12px' }}
              >
                Back
              </button>

              <button
                type="button"
                onClick={handleResend}
                disabled={resendCooldown > 0}
                style={{
                  background: 'none',
                  border: 'none',
                  color: resendCooldown > 0 ? '#9CA3AF' : '#7138E8',
                  fontWeight: 600,
                  cursor: resendCooldown > 0 ? 'default' : 'pointer',
                }}
              >
                {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : 'Resend Code'}
              </button>
            </div>
          </form>
        )}

        {/* Security Info Footer */}
        <div style={{
          marginTop: '24px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          color: '#6B7280',
          fontSize: '11px',
          textAlign: 'center',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: '14px', color: '#16A34A' }}>
            lock
          </span>
          <span>Integrated with JCER ERP Identity System</span>
        </div>
      </div>

      {/* College Footer */}
      <div style={{ marginTop: '24px', color: '#9CA3AF', fontSize: '11.5px', textAlign: 'center' }}>
        © 2026 Jain College of Engineering & Research, Belagavi. All rights reserved.
      </div>
    </div>
  );
}
