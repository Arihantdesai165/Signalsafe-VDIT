/* ============================================================
   SignalSafe Campus – Authentication & Session Controller
   Integrated with JCER ERP Identity System
   ============================================================ */

const SignalSafeAuth = {
    user: null,
    resendTimer: null,
    resendCooldown: 0,
    pendingEmail: '',
    pendingRole: '',

    init() {
        this.setupFetchInterceptor();
        this.bindEvents();
        this.checkSessionOnLoad();
    },

    // 1. Transparent Fetch Interceptor for Automatic Auth Headers & 401 Session Expiry
    setupFetchInterceptor() {
        const originalFetch = window.fetch;
        const self = this;

        window.fetch = async function (url, options = {}) {
            options = options || {};
            options.headers = options.headers || {};
            options.credentials = 'same-origin';

            const token = localStorage.getItem('signalsafe_session_token');
            if (token) {
                if (options.headers instanceof Headers) {
                    if (!options.headers.has('Authorization')) {
                        options.headers.set('Authorization', `Bearer ${token}`);
                    }
                } else if (Array.isArray(options.headers)) {
                    options.headers.push(['Authorization', `Bearer ${token}`]);
                } else {
                    options.headers['Authorization'] = options.headers['Authorization'] || `Bearer ${token}`;
                }
            }

            try {
                const response = await originalFetch(url, options);

                // If any protected API returns 401 Unauthorized, automatically handle session expiration
                if (response.status === 401 && typeof url === 'string' && url.includes('/api/') && !url.includes('/api/auth/login')) {
                    self.handleSessionExpired();
                }

                return response;
            } catch (err) {
                throw err;
            }
        };
    },

    // 2. Initial Session Check on Load
    async checkSessionOnLoad() {
        const token = localStorage.getItem('signalsafe_session_token');

        // Check if session URL parameters indicate expiration
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('expired') === 'true') {
            this.showLoginView();
            this.showLoginError('Your session has expired. Please sign in again using your JCER ERP account.');
            window.history.replaceState({}, document.title, window.location.pathname);
            return;
        }

        // If no token stored, show Login Page directly
        if (!token) {
            this.showLoginView();
            return;
        }

        try {
            const res = await fetch('/api/auth/me', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (res.ok) {
                const data = await res.json();
                if (data.authenticated && data.user) {
                    this.user = data.user;
                    localStorage.setItem('signalsafe_user', JSON.stringify(data.user));
                    this.showDashboardView(data.user);
                    return;
                }
            }
            // Invalid / expired session
            this.clearLocalSession();
            this.showLoginView();
        } catch (e) {
            console.warn('Session verification check failed:', e);
            this.showLoginView();
        }
    },

    // 3. UI View Switchers
    showLoginView() {
        const loginView = document.getElementById('signalsafe-login-view');
        const dashboardApp = document.getElementById('signalsafe-dashboard-app');

        if (dashboardApp) {
            dashboardApp.classList.add('hidden');
            dashboardApp.classList.remove('flex');
            dashboardApp.style.setProperty('display', 'none', 'important');
        }
        if (loginView) {
            loginView.classList.remove('hidden');
            loginView.classList.add('flex');
            loginView.style.setProperty('display', 'flex', 'important');
        }

        this.showCredentialsStep();
    },

    showDashboardView(user) {
        const loginView = document.getElementById('signalsafe-login-view');
        const dashboardApp = document.getElementById('signalsafe-dashboard-app');

        if (loginView) {
            loginView.classList.add('hidden');
            loginView.classList.remove('flex');
            loginView.style.setProperty('display', 'none', 'important');
        }
        if (dashboardApp) {
            dashboardApp.classList.remove('hidden');
            dashboardApp.classList.add('flex');
            dashboardApp.style.setProperty('display', 'flex', 'important');
        }

        this.applyUserDataToDashboard(user);
        if (window.KavachApp && typeof window.KavachApp.initDashboard === 'function') {
            window.KavachApp.initDashboard();
        }
    },

    applyUserDataToDashboard(user) {
        if (!user) return;

        const displayName = user.name || user.email || 'Campus User';
        const rawRole = (user.role || 'STUDENT').toUpperCase();
        let roleLabel = 'Student';
        if (rawRole === 'TEACHER' || rawRole === 'FACULTY') roleLabel = 'Faculty Member';
        else if (rawRole === 'ADMIN' || rawRole === 'SUPER_ADMIN') roleLabel = 'Security Admin';
        else if (rawRole === 'HOD') roleLabel = 'Head of Dept';
        else if (rawRole === 'PRINCIPAL') roleLabel = 'Principal';
        else if (rawRole === 'DEAN') roleLabel = 'Dean';

        const dept = user.department ? ` · ${user.department}` : '';

        // Sidebar user details
        const nameEl = document.getElementById('user-display-name');
        const roleEl = document.getElementById('user-display-role');
        const avatarEl = document.getElementById('user-display-avatar');
        const welcomeHeading = document.getElementById('welcome-user-heading');

        if (nameEl) nameEl.textContent = displayName;
        if (roleEl) roleEl.textContent = `${roleLabel}${dept}`;
        if (welcomeHeading) welcomeHeading.textContent = `Welcome back, ${displayName}!`;

        document.querySelectorAll('.user-student-name').forEach(el => {
            el.textContent = displayName;
        });

        if (avatarEl) {
            const initials = displayName
                .split(' ')
                .map(part => part[0])
                .join('')
                .toUpperCase()
                .slice(0, 2) || 'SS';
            avatarEl.textContent = initials;
        }

        // Mobile header user tag
        const mobileUserTag = document.getElementById('mobile-user-tag');
        if (mobileUserTag) mobileUserTag.textContent = displayName.split(' ')[0];
    },

    // 4. Login Card Step Switchers (Credentials vs. Staff Daily OTP)
    showCredentialsStep() {
        const credStep = document.getElementById('login-step-credentials');
        const otpStep = document.getElementById('login-step-daily-otp');
        const errorAlert = document.getElementById('login-error-alert');

        if (credStep) credStep.classList.remove('hidden');
        if (otpStep) otpStep.classList.add('hidden');
        if (errorAlert) errorAlert.classList.add('hidden');
    },

    showDailyOtpStep(email, role, message) {
        const credStep = document.getElementById('login-step-credentials');
        const otpStep = document.getElementById('login-step-daily-otp');
        const errorAlert = document.getElementById('login-error-alert');

        if (credStep) credStep.classList.add('hidden');
        if (otpStep) otpStep.classList.remove('hidden');
        if (errorAlert) errorAlert.classList.add('hidden');

        this.pendingEmail = email;
        this.pendingRole = role;

        const emailDisplay = document.getElementById('otp-pending-email');
        const roleDisplay = document.getElementById('otp-pending-role');
        const otpInput = document.getElementById('login-daily-otp');

        if (emailDisplay) emailDisplay.textContent = email;
        if (roleDisplay) roleDisplay.textContent = (role || 'STAFF').toUpperCase();
        if (otpInput) {
            otpInput.value = '';
            setTimeout(() => otpInput.focus(), 150);
        }

        this.startResendCooldown(60);
    },

    startResendCooldown(seconds) {
        this.resendCooldown = seconds;
        const resendBtn = document.getElementById('btn-resend-otp');
        const resendTimerText = document.getElementById('otp-resend-timer');

        if (this.resendTimer) clearInterval(this.resendTimer);

        if (resendBtn) resendBtn.disabled = true;
        if (resendTimerText) resendTimerText.textContent = `(${this.resendCooldown}s)`;

        this.resendTimer = setInterval(() => {
            this.resendCooldown -= 1;
            if (this.resendCooldown <= 0) {
                clearInterval(this.resendTimer);
                if (resendBtn) resendBtn.disabled = false;
                if (resendTimerText) resendTimerText.textContent = '';
            } else {
                if (resendTimerText) resendTimerText.textContent = `(${this.resendCooldown}s)`;
            }
        }, 1000);
    },

    // 5. Form Submissions
    async handleLoginSubmit(e) {
        e.preventDefault();
        const emailInput = document.getElementById('login-email');
        const passInput = document.getElementById('login-password');
        const submitBtn = document.getElementById('btn-login-submit');

        const email = emailInput ? emailInput.value.trim() : '';
        const password = passInput ? passInput.value : '';

        if (!email || !password) {
            this.showLoginError('Please enter both your User ID / Email and password.');
            return;
        }

        this.setButtonLoading(submitBtn, true, 'Signing In Securely...');
        this.hideLoginError();

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json().catch(() => ({}));

            if (!res.ok) {
                const errorMsg = data.detail || data.error || (
                    res.status === 503
                        ? 'JCER ERP authentication service is currently unreachable. Please verify the ERP backend is online.'
                        : 'Invalid credentials or authentication error.'
                );
                this.showLoginError(errorMsg);
                return;
            }

            // Case A: Staff Daily OTP Required
            if (data.requiresDailyOtp) {
                this.showDailyOtpStep(data.email || email, data.role || 'STAFF', data.message);
                return;
            }

            // Case B: Direct Login Success (Student / Verified Staff)
            if (data.success && data.token && data.user) {
                localStorage.setItem('signalsafe_session_token', data.token);
                localStorage.setItem('signalsafe_user', JSON.stringify(data.user));
                this.user = data.user;
                this.showDashboardView(data.user);
            } else {
                this.showLoginError(data.message || 'Authentication failed. Please check credentials.');
            }
        } catch (err) {
            console.error('Sign in error:', err);
            this.showLoginError('Unable to connect to the authentication service. Please check your network connection.');
        } finally {
            this.setButtonLoading(submitBtn, false, 'Sign In Securely');
        }
    },

    async handleVerifyOtpSubmit(e) {
        e.preventDefault();
        const otpInput = document.getElementById('login-daily-otp');
        const verifyBtn = document.getElementById('btn-verify-otp');
        const otp = otpInput ? otpInput.value.trim() : '';

        if (!otp || otp.length !== 6) {
            this.showLoginError('Please enter a valid 6-digit verification code.');
            return;
        }

        this.setButtonLoading(verifyBtn, true, 'Verifying Daily OTP...');
        this.hideLoginError();

        try {
            const res = await fetch('/api/auth/verify-daily-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: this.pendingEmail, otp })
            });

            const data = await res.json().catch(() => ({}));

            if (!res.ok) {
                const errorMsg = data.detail || data.error || 'Invalid or expired OTP code. Please try again.';
                this.showLoginError(errorMsg);
                return;
            }

            if (data.success && data.token && data.user) {
                localStorage.setItem('signalsafe_session_token', data.token);
                localStorage.setItem('signalsafe_user', JSON.stringify(data.user));
                this.user = data.user;
                this.showDashboardView(data.user);
            } else {
                this.showLoginError(data.message || 'Daily OTP verification failed.');
            }
        } catch (err) {
            console.error('Daily OTP verification error:', err);
            this.showLoginError('Failed to communicate with authentication service.');
        } finally {
            this.setButtonLoading(verifyBtn, false, 'Verify & Access Portal');
        }
    },

    async handleResendOtp() {
        if (this.resendCooldown > 0) return;

        const resendBtn = document.getElementById('btn-resend-otp');
        this.setButtonLoading(resendBtn, true, 'Sending...');

        try {
            const res = await fetch('/api/auth/resend-daily-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: this.pendingEmail })
            });

            const data = await res.json().catch(() => ({}));

            if (res.ok && data.success) {
                this.startResendCooldown(60);
                this.showLoginSuccess('A fresh 6-digit OTP code was sent to your registered JCER email.');
            } else {
                this.showLoginError(data.detail || data.error || 'Unable to resend Daily OTP at this time.');
            }
        } catch (err) {
            this.showLoginError('Network error while requesting fresh OTP.');
        } finally {
            this.setButtonLoading(resendBtn, false, 'Resend Code');
        }
    },

    async handleLogout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } catch (err) {
            console.warn('Logout API invocation failed:', err);
        }

        this.clearLocalSession();
        this.showLoginView();
        this.showLoginSuccess('You have successfully signed out of SignalSafe Campus.');
    },

    handleSessionExpired() {
        this.clearLocalSession();
        this.showLoginView();
        this.showLoginError('Your session has expired. Please sign in again using your JCER ERP credentials.');
    },

    clearLocalSession() {
        localStorage.removeItem('signalsafe_session_token');
        localStorage.removeItem('signalsafe_user');
        sessionStorage.clear();
        this.user = null;
    },

    // 6. Helpers
    showLoginError(message) {
        const alertBox = document.getElementById('login-error-alert');
        const alertMsg = document.getElementById('login-error-message');
        const successBox = document.getElementById('login-success-alert');

        if (successBox) successBox.classList.add('hidden');

        if (alertBox && alertMsg) {
            alertMsg.textContent = message;
            alertBox.classList.remove('hidden');
        }
    },

    showLoginSuccess(message) {
        const successBox = document.getElementById('login-success-alert');
        const successMsg = document.getElementById('login-success-message');
        const alertBox = document.getElementById('login-error-alert');

        if (alertBox) alertBox.classList.add('hidden');

        if (successBox && successMsg) {
            successMsg.textContent = message;
            successBox.classList.remove('hidden');
        }
    },

    hideLoginError() {
        const alertBox = document.getElementById('login-error-alert');
        const successBox = document.getElementById('login-success-alert');
        if (alertBox) alertBox.classList.add('hidden');
        if (successBox) successBox.classList.add('hidden');
    },

    setButtonLoading(button, isLoading, text) {
        if (!button) return;
        button.disabled = isLoading;
        if (isLoading) {
            button._originalHtml = button.innerHTML;
            button.innerHTML = `
                <span class="material-symbols-outlined text-[18px] animate-spin">progress_activity</span>
                <span>${text}</span>
            `;
        } else {
            button.innerHTML = button._originalHtml || text;
        }
    },

    bindEvents() {
        // Login form
        const loginForm = document.getElementById('form-signalsafe-login');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLoginSubmit(e));
        }

        // Daily OTP form
        const otpForm = document.getElementById('form-daily-otp-verify');
        if (otpForm) {
            otpForm.addEventListener('submit', (e) => this.handleVerifyOtpSubmit(e));
        }

        // Resend OTP button
        const resendBtn = document.getElementById('btn-resend-otp');
        if (resendBtn) {
            resendBtn.addEventListener('click', () => this.handleResendOtp());
        }

        // Back to Login button
        const backBtn = document.getElementById('btn-back-to-credentials');
        if (backBtn) {
            backBtn.addEventListener('click', () => this.showCredentialsStep());
        }

        // Show/Hide password toggle
        const togglePassBtn = document.getElementById('btn-toggle-password');
        const passInput = document.getElementById('login-password');
        if (togglePassBtn && passInput) {
            togglePassBtn.addEventListener('click', () => {
                const isPassword = passInput.type === 'password';
                passInput.type = isPassword ? 'text' : 'password';
                togglePassBtn.textContent = isPassword ? 'visibility_off' : 'visibility';
            });
        }

        // Sidebar & mobile logout buttons
        document.querySelectorAll('.btn-logout-trigger').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleLogout();
            });
        });
    }
};

// Initialize immediately on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => SignalSafeAuth.init());
