# -*- coding: utf-8 -*-
"""
KAVACH – Real Time Scam Shield for Rural India
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routers import screenshot, qrcode, url, auth, incidents, screenshot_datasets, college_qr
from .utils.translations import get_all_translations

# Resolve paths - signalsafe-frontend is the only active frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REACT_DIST_DIR = os.path.join(BASE_DIR, "signalsafe-frontend", "dist")
FRONTEND_DIR = REACT_DIST_DIR if os.path.isdir(REACT_DIST_DIR) else os.path.join(BASE_DIR, "signalsafe-frontend")

app = FastAPI(
    title="SignalSafe Campus – Cybersecurity Portal",
    description="Campus fraud detection for UPI payments, QR codes, and suspicious URLs integrated with JCER ERP.",
    version="2.0.0",
)

# CORS configuration for React frontend development & JCER ERP integration
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(screenshot.router)
app.include_router(qrcode.router)
app.include_router(url.router)
app.include_router(incidents.router)
app.include_router(screenshot_datasets.router)
app.include_router(college_qr.router)


# Translation endpoint
@app.get("/api/translations/{lang}")
async def get_translations(lang: str):
    """Get all UI translations for a given language code (en, hi, kn, mr)."""
    return get_all_translations(lang)


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "SignalSafe Campus"}


NOCACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

# Mount React frontend static files and configure SPA fallback
if os.path.isdir(FRONTEND_DIR):
    # Mount Vite production assets directory if it exists
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Serve index.html for root (SPA entry)
    @app.get("/")
    async def serve_index():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file, headers=NOCACHE_HEADERS)
        return {"status": "ok", "app": "SignalSafe Campus", "message": "React production bundle not built yet."}

    # Serve SPA routes and static root files (e.g. favicon.svg, icons.svg)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            return {"error": "API route not found"}
        # Check if requested static file exists in frontend dist
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise, fall back to index.html for React Router client-side routes
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file, headers=NOCACHE_HEADERS)
        return {"error": "Page not found"}
