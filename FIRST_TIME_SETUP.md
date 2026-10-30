# 🛡️ SignalSafe Campus — First-Time Complete Setup Guide

This guide contains **every single step** required to set up and run the **SignalSafe Campus** project from scratch on another laptop or fresh development environment.

---

## 📋 System Prerequisites

Ensure the following tools are installed on the new laptop:

| Software | Minimum Version | Recommended Version | Download / Installation Link |
| :--- | :--- | :--- | :--- |
| **Python** | 3.10+ | 3.11, 3.12, or 3.14 | [python.org/downloads](https://www.python.org/downloads/) *(Check "Add Python to PATH")* |
| **Node.js & npm** | Node 18+ / npm 9+ | Node 20 LTS | [nodejs.org](https://nodejs.org/) |
| **Docker & Docker Compose** | Docker 24+ | Docker Desktop 4.25+ | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) |
| **Git** | 2.30+ | Latest | [git-scm.com](https://git-scm.com/) |

> [!IMPORTANT]
> **Windows Users**: Ensure Docker Desktop is installed, running, and configured with either WSL 2 or Hyper-V backend.

---

## ⚡ Quick Start: Automated 1-Click Setup

If you are on Windows, you can run the automated setup script from the project root:

```cmd
setup_first_time.bat
```

Or run the cross-platform Python setup automation:

```bash
python setup_first_time.py
```

This automated script will:
1. Check that Python, Node.js, and Docker are installed.
2. Create `.env` from `.env.example` if not already present.
3. Start the dedicated PostgreSQL database container on port `5434`.
4. Create and activate a Python virtual environment (`venv`).
5. Install all backend Python dependencies from `requirements.txt`.
6. Run Alembic database migrations (`alembic upgrade head`).
7. Seed initial persistence data via `scripts/migrate_json_to_postgres.py`.
8. Install frontend dependencies (`npm install`) and build the React SPA bundle.
9. Verify system health.

---

## 🛠️ Step-by-Step Manual Setup

Follow these manual steps if you prefer to set up each component individually or if you are running on macOS / Linux.

### Step 1: Clone or Copy Project
Navigate to the project root directory:
```bash
cd UPI_Fake_detection
```

---

### Step 2: Environment Configuration (`.env`)
Create your environment configuration file from the provided template:

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**Windows (CMD) / Linux / macOS:**
```bash
cp .env.example .env
```

Ensure your `.env` contains the following default working credentials:
```env
# Dedicated SignalSafe PostgreSQL Configuration
SIGNALSAFE_DB_NAME=signalsafe_db
SIGNALSAFE_DB_USER=signalsafe_user
SIGNALSAFE_DB_PASSWORD=signalsafe_secure_pass_2026
SIGNALSAFE_DB_HOST=127.0.0.1
SIGNALSAFE_DB_PORT=5434

# Full Connection URL for SQLAlchemy
SIGNALSAFE_DATABASE_URL=postgresql://signalsafe_user:signalsafe_secure_pass_2026@127.0.0.1:5434/signalsafe_db

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

# Authentication & Session Security
SIGNALSAFE_SECRET_KEY=signalsafe_campus_master_jwt_secret_key_2026_super_secure
SIGNALSAFE_TOKEN_EXPIRY_HOURS=12

# Application Server
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
```

---

### Step 3: Launch PostgreSQL via Docker
SignalSafe Campus uses a dedicated PostgreSQL 16 container running on host port `5434` (to avoid conflict with any default PostgreSQL on port `5432`).

1. Ensure **Docker Desktop** is open and running.
2. Start the database container:
   ```bash
   docker compose up -d signalsafe_postgres
   ```
3. Check that the container is healthy:
   ```bash
   docker ps
   ```
   *You should see `signalsafe_postgres` with status `Up` and port `127.0.0.1:5434->5432/tcp`.*

---

### Step 4: Python Virtual Environment & Dependencies

1. **Create Python virtual environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - **Windows (CMD):**
     ```cmd
     venv\Scripts\activate.bat
     ```
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
     *(If script execution is disabled, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Upgrade pip and install backend dependencies**:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

*Key backend libraries installed: FastAPI, Uvicorn, SQLAlchemy, Alembic, psycopg2-binary, OpenCV, zxing-cpp, pyzbar, EasyOCR, PyTorch, Pillow.*

---

### Step 5: Database Schema & Migrations

1. **Run Alembic Migrations**:
   Applies the database schema including incidents, evidence, audit logs, screenshot datasets, and college QR registry:
   ```bash
   alembic upgrade head
   ```

2. **Seed Initial / Legacy Data**:
   Migrates initial records and initializes database sequences:
   ```bash
   python scripts/migrate_json_to_postgres.py
   ```

---

### Step 6: Frontend Installation & Production Build

1. Navigate to the React frontend directory:
   ```bash
   cd signalsafe-frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Build the production bundle:
   ```bash
   npm run build
   ```
4. Return to project root:
   ```bash
   cd ..
   ```

---

## 🚀 Running the Application

### Option A: Full-Stack Unified Mode (Recommended)
FastAPI serves the backend REST API (`/api/...`) **and** the compiled React Single-Page Application (`/`) together on a single port:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

---

### Option B: Development Mode (with Hot Reloading)
For active frontend development with instant hot module replacement:

1. **Terminal 1 (Backend API)**:
   ```bash
   python -m uvicorn backend.main:app --port 8000 --reload
   ```
2. **Terminal 2 (React Vite Dev Server)**:
   ```bash
   cd signalsafe-frontend
   npm run dev
   ```
   Open **[http://localhost:5173](http://localhost:5173)** (or port printed by Vite).

---

## 🔑 Login Accounts & Role-Based Access

The application simulates the JCER ERP authentication. You can sign in using any of the following accounts with **any password**:

| Role | Email / Username | Available Features & Navigation |
| :--- | :--- | :--- |
| **CyberAdmin** | `cyberadmin@jcer.edu` | • CyberAdmin Dashboard<br/>• Incident Reports & Investigation<br/>• Dataset Management (active CSV switching)<br/>• College QR Registry (manage/approve/deactivate)<br/>• Screenshot Detector<br/>• Website Safety Checker<br/>• Malicious Link Scanner<br/>• Admin Profile & System Settings |
| **Student** | `student99@jcer.edu`<br/>*or* `student@jcer.edu` | • Student Dashboard<br/>• QR Code Security Scanner<br/>• Screenshot Detector (OCR & Verification)<br/>• Website Safety Checker<br/>• Malicious Link Scanner<br/>• Report Security Incident<br/>• Student Profile & Settings |
| **Faculty / Staff** | `faculty.cs@jcer.edu` | • Faculty Dashboard & Security Tools<br/>• Daily OTP Verification Simulation |

---

## 🧪 Verification & Test Suites

Run the automated test suites to verify that all modules are operating with 100% test pass rate:

```bash
# 1. Verify React Frontend & Backend Integration
python test_react_integration.py

# 2. Verify College Payment QR Registry & CyberAdmin Management
python test_college_qr_registry.py

# 3. Verify Dark-Theme QR Decoding & Multi-Engine Verification
python test_dark_theme_qr_and_registry.py

# 4. Verify CyberAdmin Navigation Configuration
python test_cyberadmin_sidebar_navigation.py

# 5. Verify Screenshot Detector OCR & Dataset Matching
python test_screenshot_detector_ocr_and_verification.py

# 6. Verify Authentication & Role-Based Access Control
python test_signalsafe_auth.py

# 7. Verify Database Persistence & Audit Logging
python test_database_and_persistence.py
```

---

## ❓ Troubleshooting & FAQs

### 1. `Docker: Error response from daemon: Ports are not available: exposing port 5434`
Another process or older container is using port `5434`.
- Stop existing containers: `docker stop signalsafe_postgres && docker rm signalsafe_postgres`
- Or find and kill the process:
  - Windows: `netstat -ano | findstr :5434` then `taskkill /F /PID <PID>`
  - Linux/Mac: `lsof -i :5434` then `kill -9 <PID>`

### 2. `EasyOCR: Initializing EasyOCR Reader (English)... takes time on first run`
On the very first OCR analysis, EasyOCR downloads the detection and recognition models (`craft_mlt_25k.pth` and `english_g2.pth`, ~45 MB total) to `~/.EasyOCR/model/`. Subsequent runs load instantly from local cache.

### 3. `Port 8000 already in use`
Find and terminate the process holding port 8000:
- Windows: `netstat -ano | findstr :8000` then `taskkill /F /PID <PID>`
- Linux/Mac: `kill -9 $(lsof -t -i:8000)`

### 4. `Alembic: Can't locate revision identified by 'head'`
Ensure your virtual environment is active, you are in the project root containing `alembic.ini`, and your Docker database is running:
```bash
docker compose up -d signalsafe_postgres
alembic current
alembic upgrade head
```

### 5. `Vite: memory allocation failed / JavaScript heap out of memory`
If building on a machine with tight RAM/paging limit:
```bash
cd signalsafe-frontend
node --max-old-space-size=1024 node_modules/vite/bin/vite.js build
```

---

## 📁 Repository Architecture Overview

```
UPI_Fake_detection/
├── backend/
│   ├── database/             # SQLAlchemy engine, session pool, models
│   ├── routes/ & routers/    # FastAPI routers (auth, qrcode, screenshot, incidents, college_qr)
│   ├── services/             # Core business engines (qrcode, screenshot, college_qr, auth)
│   ├── utils/                # OCR processing, ML classification, scoring
│   └── main.py               # Application entry point & static SPA mounting
├── signalsafe-frontend/
│   ├── src/                  # React 18 application source code
│   │   ├── components/       # UI components (Sidebar, TopNav, CameraModal, RiskScoreMeter)
│   │   ├── pages/            # Page views (Dashboard, QrSecurity, Screenshot, CollegeQrManagement)
│   │   └── services/api.js   # Centralized frontend API client
│   └── dist/                 # Production compiled SPA bundle (served by FastAPI)
├── alembic/                  # Alembic database migration revisions
├── datasets/                 # Real & test QR codes and screenshot CSV datasets
├── scripts/                  # Data migration and maintenance utilities
├── docker-compose.yml        # Dedicated PostgreSQL 16 container definition
├── requirements.txt          # Python backend dependencies
├── setup_first_time.bat      # 1-Click automated Windows setup script
├── setup_first_time.py       # Cross-platform automated setup script
└── FIRST_TIME_SETUP.md       # Complete master setup guide (this file)
```

