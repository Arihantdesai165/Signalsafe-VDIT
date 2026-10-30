# -*- coding: utf-8 -*-
"""
SignalSafe Campus - Automated First-Time Setup Script.

Automates the complete initialization of SignalSafe Campus on a new machine:
1. Verifies prerequisites (Python, Node.js, Docker).
2. Initializes .env configuration.
3. Launches dedicated PostgreSQL database container via Docker Compose.
4. Waits for PostgreSQL database readiness.
5. Installs backend dependencies from requirements.txt.
6. Executes Alembic database migrations.
7. Seeds initial database records from legacy persistence.
8. Installs frontend npm packages and builds the production React SPA bundle.
9. Performs an automated health check.
"""

import os
import sys
import time
import shutil
import socket
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "signalsafe-frontend")
ENV_EXAMPLE = os.path.join(BASE_DIR, ".env.example")
ENV_FILE = os.path.join(BASE_DIR, ".env")


def print_step(step_num: int, title: str):
    print("\n" + "=" * 70)
    print(f" [{step_num}/8] {title}")
    print("=" * 70)


def run_cmd(cmd, cwd=BASE_DIR, env=None, check=True):
    """Executes a shell command with real-time output and error checking."""
    print(f"-> Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    shell = isinstance(cmd, str)
    res = subprocess.run(cmd, cwd=cwd, env=env or os.environ.copy(), shell=shell)
    if check and res.returncode != 0:
        print(f"\n[ERROR] Command failed with exit code {res.returncode}: {cmd}")
        sys.exit(res.returncode)
    return res.returncode


def check_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Checks whether a TCP port is open and accepting connections."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def main():
    print("*" * 70)
    print("    SIGNALSAFE CAMPUS - AUTOMATED FIRST-TIME SETUP RUNNER")
    print("*" * 70)

    # 1. Check Prerequisites
    print_step(1, "Checking System Prerequisites")
    print(f"Python executable: {sys.executable}")
    print(f"Python version   : {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("[ERROR] Python 3.10 or higher is required.")
        sys.exit(1)

    node_ver = shutil.which("node")
    npm_ver = shutil.which("npm")
    docker_ver = shutil.which("docker")

    if not node_ver or not npm_ver:
        print("[ERROR] Node.js and npm must be installed and added to PATH. Download from https://nodejs.org/")
        sys.exit(1)
    print(f"Found Node.js: {node_ver}")
    print(f"Found npm    : {npm_ver}")

    if not docker_ver:
        print("[WARNING] Docker not found in PATH. Make sure Docker Desktop is installed and running.")
    else:
        print(f"Found Docker : {docker_ver}")

    # 2. Setup .env
    print_step(2, "Configuring Environment Variables (.env)")
    if not os.path.exists(ENV_FILE):
        if os.path.exists(ENV_EXAMPLE):
            print(f"Copying {ENV_EXAMPLE} -> {ENV_FILE}")
            shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
        else:
            print(f"Generating default {ENV_FILE}")
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(
                    "SIGNALSAFE_DB_NAME=signalsafe_db\n"
                    "SIGNALSAFE_DB_USER=signalsafe_user\n"
                    "SIGNALSAFE_DB_PASSWORD=signalsafe_secure_pass_2026\n"
                    "SIGNALSAFE_DB_HOST=127.0.0.1\n"
                    "SIGNALSAFE_DB_PORT=5434\n"
                    "SIGNALSAFE_DATABASE_URL=postgresql://signalsafe_user:signalsafe_secure_pass_2026@127.0.0.1:5434/signalsafe_db\n"
                    "SIGNALSAFE_SECRET_KEY=signalsafe_campus_master_jwt_secret_key_2026_super_secure\n"
                    "SIGNALSAFE_TOKEN_EXPIRY_HOURS=12\n"
                    "HOST=127.0.0.1\n"
                    "PORT=8000\n"
                    "ENVIRONMENT=development\n"
                )
        print("-> .env file successfully created.")
    else:
        print("-> Existing .env file found; preserving settings.")

    # 3. Start PostgreSQL via Docker Compose
    print_step(3, "Starting Dedicated PostgreSQL 16 Database via Docker")
    run_cmd(["docker", "compose", "up", "-d", "signalsafe_postgres"])

    print("Waiting for PostgreSQL on 127.0.0.1:5434 to become ready...")
    ready = False
    for i in range(25):
        if check_port_open("127.0.0.1", 5434):
            ready = True
            print(f"-> PostgreSQL is ready on port 5434! (detected in {i+1}s)")
            break
        time.sleep(1)

    if not ready:
        print("[WARNING] PostgreSQL port 5434 did not respond within 25 seconds.")
        print("Check Docker container status with: docker ps")

    # 4. Install Python Dependencies
    print_step(4, "Installing Backend Dependencies (requirements.txt)")
    run_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run_cmd([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 5. Database Schema Migrations (Alembic)
    print_step(5, "Applying Alembic Database Migrations")
    run_cmd([sys.executable, "-m", "alembic", "upgrade", "head"])

    # 6. Seed Initial Data
    print_step(6, "Seeding Initial Persistence Data")
    migration_script = os.path.join(BASE_DIR, "scripts", "migrate_json_to_postgres.py")
    if os.path.exists(migration_script):
        run_cmd([sys.executable, migration_script])

    # 7. Install Frontend Dependencies & Build Production SPA
    print_step(7, "Installing Frontend Packages & Building React SPA")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    run_cmd([npm_cmd, "install"], cwd=FRONTEND_DIR)
    run_cmd([npm_cmd, "run", "build"], cwd=FRONTEND_DIR)

    # 8. Health Check Verification
    print_step(8, "Verifying System Readiness")
    dist_index = os.path.join(FRONTEND_DIR, "dist", "index.html")
    if os.path.exists(dist_index):
        print(f"-> Production React bundle verified at: {dist_index}")
    else:
        print("[WARNING] Production React bundle not found at dist/index.html")

    print("\n" + "*" * 70)
    print("   [SUCCESS] SIGNALSAFE CAMPUS SETUP COMPLETED SUCCESSFULLY! ")
    print("*" * 70)
    print("\nTo start the unified application server, run:")
    print(f"   {sys.executable} -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
    print("\nThen open your browser at: http://localhost:8000")
    print("\nTest User Accounts (Any password):")
    print("  * CyberAdmin: cyberadmin@jcer.edu (Access to registry, datasets, and admin dashboard)")
    print("  * Student   : student99@jcer.edu   (Access to QR security, screenshot detector, and student tools)")
    print("*" * 70 + "\n")


if __name__ == "__main__":
    main()
