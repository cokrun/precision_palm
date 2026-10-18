#!/usr/bin/env bash
# ==============================================================================
# Precision Palm Enterprise OS - Clean Code Distribution Script
# Target: Cloud_terbaru (GCP) & github_terbaru (GitHub)
# ==============================================================================

set -e

SOURCE_DIR="$(pwd)"
PARENT_DIR="$(dirname "$SOURCE_DIR")"
CLOUD_DEST="$PARENT_DIR/Cloud_terbaru"
GITHUB_DEST="$PARENT_DIR/github_terbaru"

echo "=========================================================="
echo "🌴 PRECISION PALM: CLEAN CODE & DISTRIBUTE TO CLOUD & GITHUB"
echo "Source: $SOURCE_DIR"
echo "Cloud Target: $CLOUD_DEST"
echo "GitHub Target: $GITHUB_DEST"
echo "=========================================================="

# 1. BERSIHKAN CACHE DAN FILE SAMPAH DARI SUMBER
echo "🧹 [1/5] Membersihkan cache Python dan file temporary..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "Thumbs.db" -delete 2>/dev/null || true
find . -type f -name "*.log" -delete 2>/dev/null || true

# 2. BUAT / RESET DIREKTORI TUJUAN
echo "📁 [2/5] Menyiapkan folder tujuan..."
rm -rf "$CLOUD_DEST" "$GITHUB_DEST"
mkdir -p "$CLOUD_DEST" "$GITHUB_DEST"

# 3. SALIN KE FOLDER Cloud_terbaru (UNTUK GOOGLE CLOUD)
echo "☁️  [3/5] Mengemas distribusi untuk Google Cloud (Cloud_terbaru)..."
rsync -av --progress ./ "$CLOUD_DEST/" \
    --exclude=".git" \
    --exclude="venv" \
    --exclude=".venv" \
    --exclude="env" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="github_terbaru" \
    --exclude="Cloud_terbaru"

# Pastikan file konfigurasi GCP ada di Cloud_terbaru
cat << 'EOF' > "$CLOUD_DEST/app.yaml"
runtime: python311
instance_class: F2
entrypoint: gunicorn -b :$PORT app:app --workers 3 --threads 4 --timeout 120

env_variables:
  FLASK_ENV: "production"
  GOOGLE_CLOUD_PROJECT: "palm-project-511008"
  BIGQUERY_DATASET: "precision_palm_dw"
  GCS_SPATIAL_BUCKET: "palm-spatial-assets-511008"
  GEMINI_MODEL: "gemini-3.8-flash"
EOF

# 4. SALIN KE FOLDER github_terbaru DENGAN SANITASI KETAT
echo "🐙 [4/5] Mengemas distribusi untuk GitHub (github_terbaru)..."
rsync -av --progress ./ "$GITHUB_DEST/" \
    --exclude=".git" \
    --exclude="venv" \
    --exclude=".venv" \
    --exclude="env" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude="*.pem" \
    --exclude="*service_account*.json" \
    --exclude="key*.json" \
    --exclude=".env" \
    --exclude="github_terbaru" \
    --exclude="Cloud_terbaru"

# Pasang .gitignore standar enterprise di github_terbaru
cat << 'EOF' > "$GITHUB_DEST/.gitignore"
# Byte-compiled / optimized / DLL files
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

# Databases & runtime local logs
*.sqlite3-journal
*.log
local_test_uploads/

# OS Specific
.DS_Store
Thumbs.db
EOF

# Pasang .env.example di github_terbaru
cat << 'EOF' > "$GITHUB_DEST/.env.example"
# Precision Palm Enterprise OS - Environment Configuration Template
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=change-this-to-a-secure-random-key-in-production

# Google Cloud Platform & AI Configuration
GOOGLE_CLOUD_PROJECT=precision-palm-enterprise-2026
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service_account.json
GCS_BUCKET_NAME=precision-palm-storage

# Gemini & Vertex AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash

# Database Configuration
DATABASE_URL=sqlite:///database/precision_palm.db
BIGQUERY_DATASET=precision_palm_esg
EOF

# 5. VERIFIKASI AKHIR
echo "✅ [5/5] Memeriksa hasil distribusi..."
echo "----------------------------------------------------------"
echo "Ringkasan Folder Cloud_terbaru:"
ls -lh "$CLOUD_DEST" | head -n 12
echo "----------------------------------------------------------"
echo "Ringkasan Folder github_terbaru:"
ls -lh "$GITHUB_DEST" | head -n 12
echo "=========================================================="
echo "🎉 PROSES SELESAI DENGAN SUKSES & BERSIH (CLEAN CODE)!"
echo "=========================================================="
