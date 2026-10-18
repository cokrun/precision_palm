import sqlite3
import json

conn = sqlite3.connect('precision_palm.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r['name'] for r in cur.fetchall()]
print("Tables in precision_palm.db:", tables)

for t in ['estates', 'concessions', 'pendaftaran', 'dossiers', 'cadastral_dossiers']:
    if t in tables:
        cur.execute(f"SELECT count(*) as c FROM {t}")
        cnt = cur.fetchone()['c']
        cur.execute(f"SELECT * FROM {t} LIMIT 3")
        rows = [dict(r) for r in cur.fetchall()]
        print(f"\n--- Table {t} (total {cnt}) ---")
        if rows:
            print("Columns:", list(rows[0].keys()))
            print("First row:", json.dumps(rows[0], indent=2, default=str))

conn.close()
