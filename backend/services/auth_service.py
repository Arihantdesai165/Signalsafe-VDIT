# -*- coding: utf-8 -*-
"""
SignalSafe Campus - ERP Authentication Service
Delegated authentication provider connecting to JCER ERP backend API.
Manages secure SignalSafe sessions with isolated JWT secrets.
"""

import os
import time
import logging
from typing import Optional, Dict, Any
import jwt
import httpx
from fastapi import Request, Header, HTTPException, status, Depends

logger = logging.getLogger("signalsafe.auth")

# Configuration from environment with secure defaults
JCER_ERP_API_URL = os.getenv("JCER_ERP_API_URL", "http://localhost:5000/api").rstrip("/")
SIGNALSAFE_JWT_SECRET = os.getenv("SIGNALSAFE_JWT_SECRET", "signalsafe_campus_master_secret_2026_isolated_key")
SIGNALSAFE_JWT_ALGORITHM = os.getenv("SIGNALSAFE_JWT_ALGORITHM", "HS256")
SIGNALSAFE_JWT_EXPIRY_HOURS = int(os.getenv("SIGNALSAFE_JWT_EXPIRY_HOURS", "24"))
ERP_REQUEST_TIMEOUT = float(os.getenv("ERP_REQUEST_TIMEOUT", "6.0"))
CYBERADMIN_EMAILS_ENV = os.getenv("CYBERADMIN_EMAILS", "cyberadmin@jcer.edu.in,admin.security@jcer.edu.in")
AUTHORIZED_CYBERADMIN_EMAILS = {
    e.strip().lower() for e in CYBERADMIN_EMAILS_ENV.split(",") if e.strip()
}
AUTHORIZED_CYBERADMIN_ROLES = {"CYBERADMIN"}


class ERPConnectionException(HTTPException):
    """Raised when the JCER ERP authentication service is unreachable."""
    def __init__(self, detail: str = None):
        msg = detail or (
            f"JCER ERP authentication service is currently unreachable. "
            f"Please verify that the JCER ERP backend is running at {JCER_ERP_API_URL}."
        )
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=msg)


class ERPAuthException(HTTPException):
    """Raised when ERP returns an authentication error (400, 401, 403, 429)."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


def generate_signalsafe_session(erp_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates an independent SignalSafe JWT session from an authenticated ERP user profile.
    NEVER stores or reuses ERP JWT tokens.
    """
    user_id = str(erp_user.get("id") or "")
    email = str(erp_user.get("email") or "").strip().lower()
    raw_role = str(erp_user.get("role") or "STUDENT").upper().strip()

    # Authoritative role resolution: ERP direct CYBERADMIN role or authorized email mapping
    if raw_role in AUTHORIZED_CYBERADMIN_ROLES or email in AUTHORIZED_CYBERADMIN_EMAILS:
        role = "CYBERADMIN"
    else:
        role = raw_role
    
    first_name = erp_user.get("firstName") or ""
    last_name = erp_user.get("lastName") or ""
    full_name = erp_user.get("name") or f"{first_name} {last_name}".strip() or email

    dept = erp_user.get("department")
    dept_name = ""
    if isinstance(dept, dict):
        dept_name = dept.get("name") or dept.get("code") or ""
    elif isinstance(dept, str):
        dept_name = dept

    now = int(time.time())
    exp = now + (SIGNALSAFE_JWT_EXPIRY_HOURS * 3600)

    payload = {
        "sub": user_id,
        "id": user_id,
        "erp_user_id": user_id,
        "email": email,
        "name": full_name,
        "role": role,
        "department": dept_name,
        "iat": now,
        "exp": exp,
        "iss": "SignalSafe-Campus",
    }

    token = jwt.encode(payload, SIGNALSAFE_JWT_SECRET, algorithm=SIGNALSAFE_JWT_ALGORITHM)

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_id,
            "email": email,
            "name": full_name,
            "role": role,
            "department": dept_name,
        },
        "expires_in": SIGNALSAFE_JWT_EXPIRY_HOURS * 3600,
    }


def verify_signalsafe_token(token: str) -> Dict[str, Any]:
    """
    Cryptographically verifies the SignalSafe session token using SignalSafe's private secret.
    """
    try:
        decoded = jwt.decode(
            token,
            SIGNALSAFE_JWT_SECRET,
            algorithms=[SIGNALSAFE_JWT_ALGORITHM],
            issuer="SignalSafe-Campus",
            options={"verify_exp": True, "verify_iss": True},
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your SignalSafe session has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token. Please sign in with your JCER ERP account.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    FastAPI dependency to protect authenticated routes.
    Checks 'Authorization: Bearer <token>' header and fallback 'signalsafe_session' cookie.
    """
    token: Optional[str] = None

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        token = request.cookies.get("signalsafe_session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in using your JCER ERP credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_signalsafe_token(token)


async def require_cyberadmin(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    FastAPI dependency ensuring the authenticated user has explicit CYBERADMIN privileges.
    Role is derived authoritatively from cryptographically verified SignalSafe token.
    Rejects students, teachers, and other non-cyberadmin roles with 403 Forbidden.
    """
    user_role = (current_user.get("role") or "").upper().strip()
    if user_role != "CYBERADMIN":
        logger.warning(
            f"Unauthorized CyberAdmin access attempt by {current_user.get('email')} with role {user_role}"
        )
        try:
            from .scan_history_service import record_audit_event
            record_audit_event(
                event_type="UNAUTHORIZED_CYBERADMIN_ACCESS",
                actor_erp_id=str(current_user.get("id") or current_user.get("email") or ""),
                actor_name=current_user.get("name") or current_user.get("email"),
                actor_role=user_role,
                target_resource_type="cyberadmin_endpoint",
                target_resource_id=None,
                outcome="DENIED",
                details={"email": current_user.get("email"), "attempted_role": user_role},
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CyberAdmin authorization required. Your account is not authorized to access campus incident administration.",
        )
    return current_user


async def authenticate_erp_user(identifier: str, password: str) -> Dict[str, Any]:
    """
    Communicates securely with the JCER ERP backend to authenticate user credentials.
    Passes credentials strictly in-memory without persistent storage.
    Respects student direct login and staff daily OTP requirements.
    """
    clean_id = (identifier or "").strip()
    clean_pass = password or ""

    if not clean_id or not clean_pass:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID / Email and password are required.",
        )

    erp_login_url = f"{JCER_ERP_API_URL}/auth/login"

    try:
        async with httpx.AsyncClient(timeout=ERP_REQUEST_TIMEOUT) as client:
            resp = await client.post(
                erp_login_url,
                json={"email": clean_id, "password": clean_pass},
                headers={"Content-Type": "application/json", "User-Agent": "SignalSafe-Backend/1.0"},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
        logger.error(f"Failed to connect to ERP backend at {erp_login_url}: {exc}")
        raise ERPConnectionException()
    except httpx.TimeoutException:
        logger.error(f"Timeout connecting to ERP backend at {erp_login_url}")
        raise ERPConnectionException("JCER ERP authentication service timed out. Please try again.")

    try:
        resp_data = resp.json()
    except Exception:
        resp_data = {}

    # Handle Successful ERP Response
    if resp.status_code == 200 and resp_data.get("success"):
        # Staff Daily OTP Required
        if resp_data.get("requiresDailyOtp"):
            return {
                "success": True,
                "requiresDailyOtp": True,
                "email": resp_data.get("email") or clean_id,
                "role": resp_data.get("role") or "STAFF",
                "message": resp_data.get("message") or "Daily OTP verification required for staff login.",
            }

        # Direct Successful Login (e.g., Student or OTP-exempt)
        erp_user = (resp_data.get("data") or {}).get("user")
        if not erp_user:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ERP authentication succeeded but returned an incomplete user profile.",
            )

        # Generate SignalSafe Session (discards ERP JWT)
        return generate_signalsafe_session(erp_user)

    # Handle ERP Error Status Codes
    error_msg = resp_data.get("error") or resp_data.get("message") or "Invalid credentials or account issue."

    if resp.status_code == 401:
        raise ERPAuthException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_msg)
    elif resp.status_code == 403:
        raise ERPAuthException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
    elif resp.status_code == 429:
        raise ERPAuthException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_msg)
    elif resp.status_code == 400:
        raise ERPAuthException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
    else:
        raise ERPAuthException(status_code=resp.status_code, detail=error_msg)


async def verify_erp_daily_otp(email: str, otp: str) -> Dict[str, Any]:
    """
    Submits a staff member's 6-digit Daily OTP to the JCER ERP backend for verification.
    """
    clean_email = (email or "").strip().lower()
    clean_otp = (otp or "").strip()

    if not clean_email or not clean_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and 6-digit OTP code are required.",
        )

    erp_otp_url = f"{JCER_ERP_API_URL}/auth/verify-daily-otp"

    try:
        async with httpx.AsyncClient(timeout=ERP_REQUEST_TIMEOUT) as client:
            resp = await client.post(
                erp_otp_url,
                json={"email": clean_email, "otp": clean_otp},
                headers={"Content-Type": "application/json", "User-Agent": "SignalSafe-Backend/1.0"},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
        logger.error(f"Failed to connect to ERP backend at {erp_otp_url}: {exc}")
        raise ERPConnectionException()
    except httpx.TimeoutException:
        raise ERPConnectionException("JCER ERP authentication service timed out.")

    try:
        resp_data = resp.json()
    except Exception:
        resp_data = {}

    if resp.status_code == 200 and resp_data.get("success"):
        erp_user = (resp_data.get("data") or {}).get("user")
        if not erp_user:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="ERP Daily OTP verified, but returned an incomplete user profile.",
            )
        return generate_signalsafe_session(erp_user)

    error_msg = resp_data.get("error") or resp_data.get("message") or "Daily OTP verification failed."
    raise ERPAuthException(status_code=resp.status_code, detail=error_msg)


async def resend_erp_daily_otp(email: str, password: Optional[str] = None) -> Dict[str, Any]:
    """
    Requests a fresh Daily OTP code from the JCER ERP backend.
    """
    clean_email = (email or "").strip().lower()
    if not clean_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required to resend OTP.",
        )

    erp_resend_url = f"{JCER_ERP_API_URL}/auth/resend-daily-otp"

    try:
        async with httpx.AsyncClient(timeout=ERP_REQUEST_TIMEOUT) as client:
            resp = await client.post(
                erp_resend_url,
                json={"email": clean_email, "password": password or ""},
                headers={"Content-Type": "application/json", "User-Agent": "SignalSafe-Backend/1.0"},
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.NetworkError) as exc:
        logger.error(f"Failed to connect to ERP backend at {erp_resend_url}: {exc}")
        raise ERPConnectionException()
    except httpx.TimeoutException:
        raise ERPConnectionException("JCER ERP authentication service timed out.")

    try:
        resp_data = resp.json()
    except Exception:
        resp_data = {}

    if resp.status_code == 200:
        return {
            "success": True,
            "message": resp_data.get("message") or "A new verification code has been sent to your email address.",
        }

    error_msg = resp_data.get("error") or resp_data.get("message") or "Failed to resend Daily OTP."
    raise ERPAuthException(status_code=resp.status_code, detail=error_msg)
