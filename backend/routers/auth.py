# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Authentication Router
Handles login, Daily OTP verification for staff, session validation, and logout.
"""

from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Response, Request, Depends, HTTPException, status

from ..services.auth_service import (
    authenticate_erp_user,
    verify_erp_daily_otp,
    resend_erp_daily_otp,
    get_current_user,
    ERPAuthException,
    ERPConnectionException,
)

router = APIRouter(prefix="/api/auth", tags=["SignalSafe Auth"])


class LoginRequest(BaseModel):
    email: str = Field(..., description="User ID, Email, or USN registered in JCER ERP")
    password: str = Field(..., description="JCER ERP Account Password")


class VerifyDailyOtpRequest(BaseModel):
    email: str = Field(..., description="Email address receiving the Daily OTP")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class ResendDailyOtpRequest(BaseModel):
    email: str = Field(..., description="Staff email address")
    password: Optional[str] = Field(None, description="Optional password if required by ERP")


@router.post("/login")
async def login_endpoint(payload: LoginRequest, response: Response, request: Request):
    """
    Direct SignalSafe login using JCER ERP credentials.
    Passes credentials securely to ERP without storage.
    Issues independent SignalSafe JWT session cookie on successful verification.
    """
    try:
        result = await authenticate_erp_user(payload.email, payload.password)
    except (ERPAuthException, ERPConnectionException) as exc:
        raise exc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected authentication error occurred: {str(e)}",
        )

    # If staff daily OTP is required, return challenge without session
    if result.get("requiresDailyOtp"):
        return result

    # Direct login success: attach HTTP-only cookie
    token = result.get("token")
    if token:
        is_https = request.url.scheme == "https"
        response.set_cookie(
            key="signalsafe_session",
            value=token,
            max_age=result.get("expires_in", 86400),
            httponly=True,
            samesite="lax",
            secure=is_https,
            path="/",
        )

    return result


@router.post("/verify-daily-otp")
async def verify_daily_otp_endpoint(payload: VerifyDailyOtpRequest, response: Response, request: Request):
    """
    Verifies staff daily 6-digit OTP code against JCER ERP.
    """
    try:
        result = await verify_erp_daily_otp(payload.email, payload.otp)
    except (ERPAuthException, ERPConnectionException) as exc:
        raise exc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Daily OTP verification error: {str(e)}",
        )

    token = result.get("token")
    if token:
        is_https = request.url.scheme == "https"
        response.set_cookie(
            key="signalsafe_session",
            value=token,
            max_age=result.get("expires_in", 86400),
            httponly=True,
            samesite="lax",
            secure=is_https,
            path="/",
        )

    return result


@router.post("/resend-daily-otp")
async def resend_daily_otp_endpoint(payload: ResendDailyOtpRequest):
    """
    Resends staff daily OTP verification code.
    """
    return await resend_erp_daily_otp(payload.email, payload.password)


@router.get("/me")
async def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Validates current SignalSafe session.
    Returns authenticated user profile.
    """
    return {
        "authenticated": True,
        "user": user,
    }


@router.post("/logout")
async def logout_endpoint(response: Response):
    """
    Terminates the SignalSafe session and clears session cookies.
    """
    response.delete_cookie(
        key="signalsafe_session",
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {
        "success": True,
        "message": "Logged out successfully from SignalSafe Campus.",
    }
