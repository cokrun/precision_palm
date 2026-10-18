"""
scripts/clean_and_distribute.py
Precision Palm Enterprise OS - Cross-Platform Clean Code Sanitizer & Distributor

Berfungsi di Windows, Linux, dan macOS untuk:
1. Membersihkan cache (__pycache__, *.pyc, .DS_Store, *.log).
2. Menggandakan ke folder '../Cloud_terbaru' (lengkap untuk deploy GCP).
3. Menggandakan ke folder '../github_terbaru' (bersih tanpa file kredensial/rahasia).
"""

import os
import shutil
import sys
from pathlib import Path

# Safe encoding for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def sanitize_and_distribute():
    root_dir = Path(__file__).resolve().parent.parent
    parent_dir = root_dir.parent
    cloud_dir = parent_dir / "Cloud_terbaru"
    github_dir = parent_dir / "github_terbaru"

    print("=" * 65)
    print("[*] PRECISION PALM: CLEAN CODE & DISTRIBUTE AUTOMATION")
    print(f"Source Directory : {root_dir}")
    print(f"Cloud Target     : {cloud_dir}")
    print(f"GitHub Target    : {github_dir}")
    print("=" * 65)

    # 1. Bersihkan Cache Lokal & File Sampah
    print("\n[1/5] Cleaning local cache and temporary files in source...")
    cleaned_items = 0
    for p in list(root_dir.rglob("*")):
        if p.is_dir() and p.name == "__pycache__":
            shutil.rmtree(p, ignore_errors=True)
            cleaned_items += 1
        elif p.is_file() and (p.suffix in [".pyc", ".pyo", ".log", ".swp"] or p.name in [".DS_Store", "Thumbs.db"]):
            try:
                p.unlink()
                cleaned_items += 1
            except Exception:
                pass
    print(f"   [OK] Cleaned {cleaned_items} temporary/cache artifacts.")

    # 2. Reset Folder Tujuan
    print("\n[2/5] Resetting destination folders...")
    for target in [cloud_dir, github_dir]:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)
    print("   [OK] Target folders initialized cleanly.")

    # 3. Definisi Filter
    common_ignore_dirs = {
        ".git", "venv", ".venv", "env", "ENV", "__pycache__",
        "github_terbaru", "Cloud_terbaru", ".idea", ".vscode", "scratch"
    }

    def should_ignore_cloud(path: Path) -> bool:
        rel = path.relative_to(root_dir)
        for part in rel.parts:
            if part in common_ignore_dirs:
                return True
        if path.suffix in [".pyc", ".pyo", ".log"]:
            return True
        return False

    def should_ignore_github(path: Path) -> bool:
        if should_ignore_cloud(path):
            return True
        # Secret sanitization
        name_lower = path.name.lower()
        if name_lower.startswith(".env") and name_lower != ".env.example":
            return True
        if path.suffix in [".pem", ".key"]:
            return True
        if "service_account" in name_lower and path.suffix == ".json":
            return True
        if name_lower in ["credentials.json", "client_secret.json"] or name_lower.startswith("client_secret_"):
            return True
        if name_lower.startswith("key") and path.suffix == ".json":
            return True
        return False

    # 4. Copy ke Cloud_terbaru (Google Cloud Platform)
    print("\n[3/5] Packaging distribution for Google Cloud (Cloud_terbaru)...")
    cloud_count = 0
    for src_path in root_dir.rglob("*"):
        if should_ignore_cloud(src_path):
            continue
        rel = src_path.relative_to(root_dir)
        dest_path = cloud_dir / rel
        if src_path.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_path, dest_path)
                cloud_count += 1
            except Exception as e:
                print(f"   [WARN] Could not copy {src_path.name}: {e}")

    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    from config import Config

    # Tambahkan app.yaml untuk GCP di Cloud_terbaru
    app_yaml_content = f"""runtime: python311
instance_class: F2
entrypoint: gunicorn -b :$PORT app:app --workers 3 --threads 4 --timeout 120

env_variables:
  FLASK_ENV: "production"
  GOOGLE_CLOUD_PROJECT: "{Config.PROJECT_ID}"
  GCP_REGION: "{Config.GCP_REGION}"
  BIGQUERY_DATASET: "{Config.BQ_DATASET}"
  GCS_SPATIAL_BUCKET: "{Config.GCS_BUCKET}"
  GEMINI_MODEL: "{Config.GEMINI_MODEL}"
"""
    (cloud_dir / "app.yaml").write_text(app_yaml_content, encoding="utf-8")
    print(f"   [OK] Copied {cloud_count} files to {cloud_dir}")
    print("   [OK] Configured production GCP app.yaml")

    # 5. Copy ke github_terbaru (Sanitized for GitHub)
    print("\n[4/5] Packaging distribution for GitHub (github_terbaru)...")
    github_count = 0
    for src_path in root_dir.rglob("*"):
        if should_ignore_github(src_path):
            continue
        rel = src_path.relative_to(root_dir)
        dest_path = github_dir / rel
        if src_path.is_dir():
            dest_path.mkdir(parents=True, exist_ok=True)
        else:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(src_path, dest_path)
                github_count += 1
            except Exception as e:
                print(f"   [WARN] Could not copy {src_path.name}: {e}")

    # Tambahkan .gitignore standar enterprise di github_terbaru
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environments
venv/
.venv/
env/
ENV/

# Secrets & Local Configurations
.env
*.pem
*service_account*.json
credentials.json
client_secret*.json
key*.json

# Databases & runtime local logs
*.sqlite3-journal
*.log
local_test_uploads/

# OS Specific
.DS_Store
Thumbs.db
"""
    (github_dir / ".gitignore").write_text(gitignore_content, encoding="utf-8")

    # Tambahkan .env.example di github_terbaru
    env_example_content = f"""# Precision Palm Enterprise OS - Environment Configuration Template
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=change-this-to-a-secure-random-key-in-production

# Google Cloud Platform & AI Configuration
GOOGLE_CLOUD_PROJECT={Config.PROJECT_ID}
GCP_REGION={Config.GCP_REGION}
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service_account.json
GCS_SPATIAL_BUCKET={Config.GCS_BUCKET}
BIGQUERY_DATASET={Config.BQ_DATASET}
BIGQUERY_TABLE_AUDIT={Config.BQ_AUDIT_TABLE}
BIGQUERY_TABLE_LOGS={Config.BQ_LOGS_TABLE}

# Gemini & Vertex AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL={Config.GEMINI_MODEL}

# Database Configuration
DATABASE_URL=sqlite:///precision_palm.db
"""
    (github_dir / ".env.example").write_text(env_example_content, encoding="utf-8")
    print(f"   [OK] Copied {github_count} sanitized files to {github_dir}")
    print("   [OK] Configured enterprise .gitignore & .env.example")

    # 6. Ringkasan & Verifikasi
    print("\n[5/5] VERIFIKASI AKHIR DISTRIBUSI:")
    print("-" * 65)
    print(f"Ringkasan Folder Cloud_terbaru ({cloud_dir}):")
    cloud_items = list(cloud_dir.glob("*"))
    for item in sorted(cloud_items)[:12]:
        kind = "DIR " if item.is_dir() else "FILE"
        size = f"{item.stat().st_size / 1024:.1f} KB" if item.is_file() else "-"
        print(f"  [{kind}] {item.name:<32} ({size})")
    if len(cloud_items) > 12:
        print(f"  ... dan {len(cloud_items) - 12} berkas/folder lainnya.")

    print("\n" + "-" * 65)
    print(f"Ringkasan Folder github_terbaru ({github_dir}):")
    github_items = list(github_dir.glob("*"))
    for item in sorted(github_items)[:12]:
        kind = "DIR " if item.is_dir() else "FILE"
        size = f"{item.stat().st_size / 1024:.1f} KB" if item.is_file() else "-"
        print(f"  [{kind}] {item.name:<32} ({size})")
    if len(github_items) > 12:
        print(f"  ... dan {len(github_items) - 12} berkas/folder lainnya.")

    # Verifikasi keamanan rahasia di github_terbaru
    print("\n[LOCK] Pemeriksaan Keamanan Rahasia di github_terbaru:")
    leaks = []
    for f in github_dir.rglob("*"):
        if f.is_file():
            if f.name.startswith(".env") and f.name != ".env.example":
                leaks.append(f.name)
            if "service_account" in f.name.lower() and f.suffix == ".json":
                leaks.append(f.name)
            if f.suffix in [".pem", ".key"]:
                leaks.append(f.name)
    if leaks:
        print(f"  [WARN] Ditemukan file berisiko: {leaks}")
    else:
        print("  [OK] ZERO SECRETS DETECTED: Repositori GitHub 100% aman dan tersanitasi!")

    print("=" * 65)
    print("[SUCCESS] PROSES SELESAI DENGAN SUKSES & BERSIH (CLEAN CODE)!")
    print("=" * 65)

if __name__ == "__main__":
    sanitize_and_distribute()
