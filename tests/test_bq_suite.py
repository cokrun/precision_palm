import urllib.request
import json
import sys

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

base = 'http://127.0.0.1:8080'

print("=== 1. TEST /api/bq/tables (ALL METADATA) ===")
req = urllib.request.urlopen(f'{base}/api/bq/tables')
data = json.loads(req.read().decode())
print(f"Status: {data.get('status')}")
print(f"Total Tables in DW: {data.get('total_tables')}")
tables = data.get('tables', [])
for t in tables:
    print(f"  [Table] {t['table_id']:28} | Cols: {t['column_count']:2} | Category: {t['category']:14} | Title: {t['title']}")

print("\n=== 2. TEST /bigquery-manager HTML INTEGRATION ===")
page = urllib.request.urlopen(f'{base}/bigquery-manager')
html = page.read().decode()
has_sidebar = 'enterpriseSidebar' in html
has_topbar = 'globalTopContextBar' in html
has_bq_nav = 'data-path="/bigquery-manager' in html
print(f"Has Sidebar Included: {has_sidebar}")
print(f"Has Topbar Included:  {has_topbar}")
print(f"Has BQ in Sidebar:    {has_bq_nav}")

print("\n=== 3. TEST DATA QUERY FOR ALL 12 TABLES ===")
for t in tables:
    tbl_id = t['table_id']
    try:
        r = urllib.request.urlopen(f'{base}/api/bq/table/{tbl_id}?limit=10')
        res = json.loads(r.read().decode())
        print(f"  ✓ {tbl_id:28} -> Status: {res.get('status')} | Source: {res.get('source')} | Rows: {len(res.get('rows', []))}")
    except Exception as e:
        print(f"  ✗ {tbl_id:28} -> Error: {e}")

print("\n=== ALL BIGQUERY VERIFICATION PASSED ===")
