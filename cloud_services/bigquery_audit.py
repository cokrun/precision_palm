# cloud_services/bigquery_audit.py
import os
import json
import hashlib
import threading
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure environment is loaded
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, '.env'))

WIB = timezone(timedelta(hours=7))

def get_wib_now() -> str:
    return datetime.now(WIB).strftime('%Y-%m-%d %H:%M:%S WIB')

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID", "palm-project-511008")
DATASET_ID = os.environ.get("BIGQUERY_DATASET", "precision_palm_dw")
TABLE_ID = "node_audit_reviews"
DB_PATH = os.path.join(ROOT_DIR, 'precision_palm.db')

logger = logging.getLogger("PrecisionPalm.BigQueryAudit")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [BQ_AUDIT] %(message)s'))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

_BQ_CLIENT_INSTANCE = None
_BQ_FAILED = False

def has_gcp_credentials():
    if os.environ.get("K_SERVICE") or os.environ.get("GAE_SERVICE"):
        return True
    cred_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_file and os.path.exists(cred_file):
        return True
    adc_win = os.path.join(os.environ.get("APPDATA", ""), "gcloud", "application_default_credentials.json")
    adc_unix = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    if os.path.exists(adc_win) or os.path.exists(adc_unix):
        return True
    return False

def _create_gcloud_credentials():
    try:
        import subprocess
        from google.oauth2.credentials import Credentials
        token = subprocess.check_output('gcloud auth print-access-token', shell=True, timeout=5).decode().strip()
        if token and token.startswith('ya29.'):
            return Credentials(token)
    except Exception:
        pass
    return None

def get_bq_client():
    global _BQ_CLIENT_INSTANCE, _BQ_FAILED
    if _BQ_FAILED:
        return None
    if _BQ_CLIENT_INSTANCE is None:
        try:
            from google.cloud import bigquery
            proj = os.environ.get("GOOGLE_CLOUD_PROJECT") or "palm-project-511008"
            if has_gcp_credentials():
                _BQ_CLIENT_INSTANCE = bigquery.Client(project=proj)
            else:
                creds = _create_gcloud_credentials()
                if creds:
                    _BQ_CLIENT_INSTANCE = bigquery.Client(project=proj, credentials=creds)
                else:
                    logger.info("Local environment without ADC or gcloud credentials detected. Dual-write using SQLite local ledger.")
                    _BQ_FAILED = True
                    return None
            logger.info(f"BigQuery Client initialized with project: {_BQ_CLIENT_INSTANCE.project}")
        except Exception as e:
            logger.warning(f"BigQuery Client init note ({e}). Continuing with SQLite local ledger dual-write.")
            _BQ_FAILED = True
            return None
    return _BQ_CLIENT_INSTANCE

def _ensure_sqlite_table():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=15.0)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS node_audit_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT,
                estate_code TEXT,
                node_title TEXT,
                verdict_answer TEXT,
                citations TEXT,
                citations_json TEXT,
                timestamp TEXT,
                sha256_hash TEXT,
                sync_status TEXT DEFAULT 'LOCAL_SAVED',
                sync_error TEXT
            );
        """)
        # Ensure optional columns exist if table was created with older schema
        cur.execute("PRAGMA table_info(node_audit_reviews);")
        existing_cols = [c[1] for c in cur.fetchall()]
        if 'citations' not in existing_cols:
            cur.execute("ALTER TABLE node_audit_reviews ADD COLUMN citations TEXT;")
        if 'citations_json' not in existing_cols:
            cur.execute("ALTER TABLE node_audit_reviews ADD COLUMN citations_json TEXT;")
        if 'sync_status' not in existing_cols:
            cur.execute("ALTER TABLE node_audit_reviews ADD COLUMN sync_status TEXT DEFAULT 'LOCAL_SAVED';")
        if 'sync_error' not in existing_cols:
            cur.execute("ALTER TABLE node_audit_reviews ADD COLUMN sync_error TEXT;")
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error ensuring SQLite table node_audit_reviews: {e}")

def _save_to_sqlite_sync(node_id, estate_code, node_title, verdict_answer, citations_str, ts, sha_hash) -> int:
    _ensure_sqlite_table()
    inserted_id = -1
    try:
        conn = sqlite3.connect(DB_PATH, timeout=15.0)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO node_audit_reviews 
            (node_id, estate_code, node_title, verdict_answer, citations, citations_json, timestamp, sha256_hash, sync_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'LOCAL_SAVED');
        """, (str(node_id), str(estate_code), str(node_title), str(verdict_answer), citations_str, citations_str, ts, sha_hash))
        conn.commit()
        inserted_id = cur.lastrowid
        conn.close()
        logger.info(f"Synchronously persisted node review {node_id} ({estate_code}) to SQLite local ledger (ID={inserted_id}).")
    except Exception as sq_err:
        logger.error(f"Synchronous SQLite persistence error: {sq_err}")
    return inserted_id

def _update_sqlite_sync_status(row_id: int, status: str, error_msg: str = None):
    if row_id <= 0:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            UPDATE node_audit_reviews 
            SET sync_status = ?, sync_error = ?
            WHERE rowid = ?;
        """, (status, error_msg, row_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Failed to update SQLite sync status: {e}")

def _background_bq_insert(row_id, node_id, estate_code, node_title, verdict_answer, citations_str, ts, sha_hash):
    client = get_bq_client()
    if not client:
        logger.info(f"BigQuery stream skipped for node {node_id} ({estate_code}) - client not connected. Safe in SQLite local ledger.")
        _update_sqlite_sync_status(row_id, 'SAVED_LOCAL_OFFLINE')
        return

    table_ref = f"{client.project}.{DATASET_ID}.{TABLE_ID}"
    try:
        from google.cloud import bigquery
        # Verify / create table if missing
        try:
            table = client.get_table(table_ref)
        except Exception:
            schema = [
                bigquery.SchemaField("node_id", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("node_title", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("estate_code", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("verdict_answer", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("citations", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("citations_json", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("sha256_hash", "STRING", mode="NULLABLE"),
                bigquery.SchemaField("timestamp", "STRING", mode="NULLABLE"),
            ]
            new_table = bigquery.Table(table_ref, schema=schema)
            table = client.create_table(new_table)
            logger.info(f"Created BigQuery table: {table_ref}")

        field_names = [f.name for f in table.schema]
        row_dict = {
            "node_id": str(node_id),
            "estate_code": str(estate_code),
            "node_title": str(node_title),
            "verdict_answer": str(verdict_answer),
            "sha256_hash": str(sha_hash),
            "timestamp": str(ts)
        }
        if "citations" in field_names:
            row_dict["citations"] = str(citations_str)
        if "citations_json" in field_names:
            row_dict["citations_json"] = str(citations_str)

        errors = client.insert_rows_json(table_ref, [row_dict])
        if errors:
            logger.error(f"[BigQuery Stream Error node_audit_reviews]: {errors}")
            _update_sqlite_sync_status(row_id, 'FAILED', str(errors))
        else:
            logger.info(f"[✓ BigQuery Stream Success]: Node review {node_id} ({estate_code}) permanently sealed in BigQuery.")
            _update_sqlite_sync_status(row_id, 'STREAMED', None)
    except Exception as err:
        logger.error(f"[Background BigQuery Error]: {err}")
        _update_sqlite_sync_status(row_id, 'FAILED', str(err))

def save_node_review_to_bigquery(node_id, estate_code, node_title, verdict_answer, citations_list):
    """
    Menyimpan hasil audit secara dual-write:
    1. WAJIB tersimpan dulu ke SQLite lokal (precision_palm.db) secara SINKRON.
    2. Background thread mengalirkan data ke Google BigQuery (precision_palm_dw).
    """
    ts = get_wib_now()
    citations_str = json.dumps(citations_list, ensure_ascii=False) if isinstance(citations_list, (list, dict)) else str(citations_list or "[]")
    
    raw_seed = f"{ts}|{node_id}|{estate_code}|{str(verdict_answer)[:100]}"
    sha_hash = hashlib.sha256(raw_seed.encode('utf-8')).hexdigest().upper()
    
    # 1. Dual-Write Step 1: Simpan Sinkron ke SQLite Lokal
    local_row_id = _save_to_sqlite_sync(node_id, estate_code, node_title, verdict_answer, citations_str, ts, sha_hash)

    # 2. Dual-Write Step 2: Luncurkan streaming ke BigQuery di background thread
    bg_thread = threading.Thread(
        target=_background_bq_insert,
        args=(local_row_id, node_id, estate_code, node_title, verdict_answer, citations_str, ts, sha_hash),
        daemon=True
    )
    bg_thread.start()

    return {
        "success": True, 
        "sha256_hash": sha_hash, 
        "timestamp": ts, 
        "storage": "BigQuery / Local Ledger",
        "local_id": local_row_id
    }

def get_latest_node_review(node_id, estate_code):
    """
    Mengambil riwayat review audit dengan prioritas:
    1. BigQuery Data Warehouse jika terotentikasi dan terkoneksi.
    2. Fallback mulus ke SQLite lokal (precision_palm.db) agar tidak pernah 404/hilang.
    """
    client = get_bq_client()
    if client:
        try:
            from google.cloud import bigquery
            query = f"""
                SELECT node_id, estate_code, node_title, verdict_answer, 
                       COALESCE(citations, citations_json, '[]') as citations_data,
                       timestamp, sha256_hash
                FROM `{client.project}.{DATASET_ID}.{TABLE_ID}`
                WHERE node_id = @node_id AND estate_code = @estate_code
                ORDER BY timestamp DESC
                LIMIT 1
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("node_id", "STRING", str(node_id)),
                    bigquery.ScalarQueryParameter("estate_code", "STRING", str(estate_code))
                ]
            )
            df = client.query(query, job_config=job_config).result()
            for r in df:
                c_json = []
                try:
                    c_json = json.loads(r.citations_data)
                except Exception:
                    c_json = [r.citations_data] if r.citations_data else []
                return {
                    "has_record": True,
                    "node_id": r.node_id,
                    "estate_code": r.estate_code,
                    "node_title": r.node_title,
                    "verdict_answer": r.verdict_answer,
                    "citations": c_json,
                    "timestamp": r.timestamp,
                    "sha256_hash": r.sha256_hash,
                    "storage": "BigQuery"
                }
        except Exception as e_bq:
            logger.warning(f"BigQuery get_latest_node_review query note ({e_bq}). Falling back to SQLite.")

    # Fallback ke SQLite lokal
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(node_audit_reviews);")
        existing_cols = [c[1] for c in cur.fetchall()]
        cite_expr = "COALESCE(citations, citations_json, '[]')" if ('citations' in existing_cols and 'citations_json' in existing_cols) else ("citations" if 'citations' in existing_cols else "citations_json")

        cur.execute(f"""
            SELECT node_id, estate_code, node_title, verdict_answer, {cite_expr}, timestamp, sha256_hash
            FROM node_audit_reviews
            WHERE node_id = ? AND estate_code = ?
            ORDER BY rowid DESC LIMIT 1;
        """, (str(node_id), str(estate_code)))
        row = cur.fetchone()
        conn.close()
        if row:
            c_json = []
            try:
                c_json = json.loads(row[4])
            except Exception:
                c_json = [row[4]] if row[4] else []
            return {
                "has_record": True,
                "success": True,
                "node_id": row[0],
                "estate_code": row[1],
                "node_title": row[2],
                "verdict_answer": row[3],
                "citations": c_json,
                "timestamp": row[5],
                "sha256_hash": row[6],
                "storage": "Local Ledger (Synchronized)"
            }
    except Exception as sq_err:
        logger.error(f"SQLite get_latest_node_review error: {sq_err}")

    # Fallback to static/data/default_state.json seed
    try:
        seed_path = os.path.join(ROOT_DIR, 'static', 'data', 'default_state.json')
        if os.path.exists(seed_path):
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed_data = json.load(f)
            reviews = seed_data.get('node_audit_reviews', [])
            for r in reviews:
                if str(r.get('node_id')) == str(node_id) and str(r.get('estate_code')) == str(estate_code):
                    c_json = r.get('citations_json') or r.get('citations') or []
                    if isinstance(c_json, str):
                        try:
                            c_json = json.loads(c_json)
                        except Exception:
                            c_json = [c_json]
                    return {
                        "has_record": True,
                        "success": True,
                        "node_id": r.get('node_id'),
                        "estate_code": r.get('estate_code'),
                        "node_title": r.get('node_title'),
                        "verdict_answer": r.get('verdict_answer'),
                        "citations": c_json,
                        "timestamp": r.get('timestamp'),
                        "sha256_hash": r.get('sha256_hash'),
                        "storage": "BigQuery Seed Hydration"
                    }
    except Exception as e_seed:
        logger.warning(f"Seed fallback error: {e_seed}")

    return {"has_record": False, "success": True}
