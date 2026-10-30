# 🛡️ How to Run SignalSafe Campus (First-Time & Daily Setup)

Follow this guide to start the **SignalSafe Campus** platform on your local machine or fresh laptop.

For the exhaustive setup reference, see [`FIRST_TIME_SETUP.md`](./FIRST_TIME_SETUP.md).

---

## ⚡ 1-Click Automated Setup (Fresh Laptop / First Time)

If you just cloned or copied this project to a new computer, run the automated setup script from the project root:

### Windows:
Double-click `setup_first_time.bat` or run:
```cmd
setup_first_time.bat
```

### macOS / Linux / Cross-Platform:
```bash
python setup_first_time.py
```

This single command handles:
1. Creating `.env` configuration with default credentials.
2. Spinning up the dedicated PostgreSQL 16 container on port `5434`.
3. Installing all backend Python dependencies.
4. Applying Alembic database migrations (`alembic upgrade head`).
5. Seeding initial persistence data (`scripts/migrate_json_to_postgres.py`).
6. Installing frontend dependencies and compiling the production React SPA bundle.

---

## 📋 Prerequisites
- **Python 3.10+** (Python 3.11, 3.12, or 3.14 recommended, with "Add to PATH" checked).
- **Node.js 18+** & npm.
- **Docker Desktop** (running).

---

## 🛠️ Manual First-Time Setup (Step-by-Step)

### 1. Environment File (`.env`)
Copy the template to create `.env`:
```bash
# Windows PowerShell:
Copy-Item .env.example .env

# Windows CMD / Linux / macOS:
cp .env.example .env
```

### 2. Start PostgreSQL Database (Docker)
SignalSafe uses an isolated PostgreSQL container running on dedicated host port `5434`:
```bash
docker compose up -d signalsafe_postgres
```
*Verify it is running with `docker ps`.*

### 3. Python Virtual Environment & Backend Packages
```bash
# Create venv
python -m venv venv

# Activate venv:
# Windows CMD:        venv\Scripts\activate.bat
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# macOS/Linux:        source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Database Migrations & Initial Seed Data
```bash
alembic upgrade head
python scripts/migrate_json_to_postgres.py
```

### 5. Build React Production Frontend
```bash
cd signalsafe-frontend
npm install
npm run build
cd ..
```

---

## 🚀 Running the Server

### Option A: Unified Production Mode (FastAPI serves Backend + React SPA)
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

### Option B: Development Mode (Vite Hot-Reloading)
- **Terminal 1 (Backend API):**
  ```bash
  python -m uvicorn backend.main:app --port 8000 --reload
  ```
- **Terminal 2 (React Frontend Dev Server):**
  ```bash
  cd signalsafe-frontend
  npm run dev
  ```
  Open: **[http://localhost:5173](http://localhost:5173)**

---

## 🔑 Login Accounts (Simulation Mode)

Sign in with **any password**:

| Role | Email | Features |
| :--- | :--- | :--- |
| **CyberAdmin** | `cyberadmin@jcer.edu` | CyberAdmin Dashboard, Incident Investigation, Dataset Management, College QR Registry (Management/Approval) |
| **Student** | `student99@jcer.edu` | Student Dashboard, QR Code Security Scanner, Screenshot Detector, Website Safety Checker, Malicious Link Scanner |
| **Faculty** | `faculty.cs@jcer.edu` | Faculty Security Dashboard & Simulated Daily OTP Verification |

---

## 🧪 Verification Commands

To confirm all components are functional:
```bash
python test_react_integration.py
python test_college_qr_registry.py
python test_dark_theme_qr_and_registry.py
python test_cyberadmin_sidebar_navigation.py
python test_screenshot_detector_ocr_and_verification.py
```
