import os
from dotenv import load_dotenv

# Muat file .env secara absolut dari direktori root aplikasi
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'), override=True)

class Config:
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "palm-project-511008")
    GCP_REGION = os.getenv("GCP_REGION", "asia-southeast2")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    GCS_BUCKET = os.getenv("GCS_SPATIAL_BUCKET", f"palm-spatial-assets-{PROJECT_ID}")
    BQ_DATASET = os.getenv("BIGQUERY_DATASET", "precision_palm_dw")
    BQ_AUDIT_TABLE = os.getenv("BIGQUERY_TABLE_AUDIT", "audit_events")
    BQ_LOGS_TABLE = os.getenv("BIGQUERY_TABLE_LOGS", "system_logs")
    PORT = int(os.getenv("PORT", 8080))
