import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('signalsafe_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState(() => localStorage.getItem('signalsafe_session_token') || null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  // Staff Daily OTP Challenge State
  const [requiresDailyOtp, setRequiresDailyOtp] = useState(false);
  const [pendingOtpEmail, setPendingOtpEmail] = useState('');
  const [pendingOtpRole, setPendingOtpRole] = useState('STAFF');
  const [otpMessage, setOtpMessage] = useState('');

  // Validate active session with backend on initial load
  const validateSession = useCallback(async () => {
    const storedToken = localStorage.getItem('signalsafe_session_token');
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await api.getMe();
      if (response && response.authenticated && response.user) {
        setUser(response.user);
        setToken(storedToken);
        localStorage.setItem('signalsafe_user', JSON.stringify(response.user));
      } else {
        throw new Error('Invalid session response');
      }
    } catch (err) {
      console.warn('Session verification error:', err.message);
      setUser(null);
      setToken(null);
      localStorage.removeItem('signalsafe_session_token');
      localStorage.removeItem('signalsafe_user');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    validateSession();

    // Listen for automatic session expiration events from API service
    const handleSessionExpired = () => {
      setUser(null);
      setToken(null);
      setAuthError('Your session has expired. Please sign in again with your JCER ERP account.');
    };

    window.addEventListener('signalsafe:session-expired', handleSessionExpired);
    return () => window.removeEventListener('signalsafe:session-expired', handleSessionExpired);
  }, [validateSession]);

  /**
   * Primary ERP Login
   */
  const login = async (email, password) => {
    setAuthError(null);
    try {
      const result = await api.login(email, password);

      // Check if Staff Daily OTP is required
      if (result.requiresDailyOtp) {
        setRequiresDailyOtp(true);
        setPendingOtpEmail(result.email || email);
        setPendingOtpRole(result.role || 'STAFF');
        setOtpMessage(result.message || 'Daily OTP verification required for staff security.');
        return { requiresDailyOtp: true };
      }

      // Direct Login Success (Students, OTP-exempt)
      if (result.success && result.token && result.user) {
        localStorage.setItem('signalsafe_session_token', result.token);
        localStorage.setItem('signalsafe_user', JSON.stringify(result.user));
        setToken(result.token);
        setUser(result.user);
        setRequiresDailyOtp(false);
        return { success: true, user: result.user };
      }

      throw new Error(result.message || 'Authentication failed. Please verify credentials.');
    } catch (err) {
      const message = err.message || 'Invalid credentials or ERP authentication service error.';
      setAuthError(message);
      throw err;
    }
  };

  /**
   * Verify Staff Daily OTP
   */
  const verifyDailyOtp = async (otp) => {
    setAuthError(null);
    try {
      const result = await api.verifyDailyOtp(pendingOtpEmail, otp);
      if (result.success && result.token && result.user) {
        localStorage.setItem('signalsafe_session_token', result.token);
        localStorage.setItem('signalsafe_user', JSON.stringify(result.user));
        setToken(result.token);
        setUser(result.user);
        setRequiresDailyOtp(false);
        setPendingOtpEmail('');
        return { success: true, user: result.user };
      }
      throw new Error(result.message || 'Invalid verification code.');
    } catch (err) {
      const message = err.message || 'OTP verification failed. Please try again.';
      setAuthError(message);
      throw err;
    }
  };

  /**
   * Resend Staff Daily OTP
   */
  const resendDailyOtp = async () => {
    setAuthError(null);
    return api.resendDailyOtp(pendingOtpEmail);
  };

  /**
   * Reset Challenge back to Credentials
   */
  const cancelOtpChallenge = () => {
    setRequiresDailyOtp(false);
    setPendingOtpEmail('');
    setOtpMessage('');
    setAuthError(null);
  };

  /**
   * Terminate Session
   */
  const logout = async () => {
    try {
      await api.logout();
    } catch (err) {
      console.warn('Logout API error:', err);
    } finally {
      setUser(null);
      setToken(null);
      setRequiresDailyOtp(false);
      localStorage.removeItem('signalsafe_session_token');
      localStorage.removeItem('signalsafe_user');
    }
  };

  const value = {
    user,
    token,
    isAuthenticated: Boolean(user && token),
    isLoading,
    authError,
    setAuthError,
    requiresDailyOtp,
    pendingOtpEmail,
    pendingOtpRole,
    otpMessage,
    login,
    verifyDailyOtp,
    resendDailyOtp,
    cancelOtpChallenge,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
