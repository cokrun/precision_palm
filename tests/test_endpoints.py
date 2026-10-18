import urllib.request
import json

def test_endpoints():
    base_url = "http://127.0.0.1:8080"
    
    # 1. Test GET /pengaturan
    print("Testing GET /pengaturan...")
    try:
        req = urllib.request.urlopen(f"{base_url}/pengaturan")
        print(f"GET /pengaturan status: {req.status}")
        assert req.status == 200
    except Exception as e:
        print(f"Error GET /pengaturan: {e}")

    # 2. Test GET /api/settings
    print("\nTesting GET /api/settings...")
    try:
        req = urllib.request.urlopen(f"{base_url}/api/settings")
        data = json.loads(req.read().decode('utf-8'))
        print(f"GET /api/settings response status: {data.get('status')}")
        print(f"Current settings: {data.get('settings')}")
        assert data.get('status') == 'success'
    except Exception as e:
        print(f"Error GET /api/settings: {e}")

    # 3. Test POST /api/settings
    print("\nTesting POST /api/settings...")
    try:
        post_data = json.dumps({"market_mode": "IDR", "audit_year": "2026"}).encode('utf-8')
        req = urllib.request.Request(f"{base_url}/api/settings", data=post_data, headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode('utf-8'))
        print(f"POST /api/settings response: {data.get('status')}")
        assert data.get('status') == 'success'
    except Exception as e:
        print(f"Error POST /api/settings: {e}")

    # 4. Test GET /api/pricing/tbs-calculation
    print("\nTesting GET /api/pricing/tbs-calculation...")
    try:
        req = urllib.request.urlopen(f"{base_url}/api/pricing/tbs-calculation")
        data = json.loads(req.read().decode('utf-8'))
        print(f"GET /api/pricing/tbs-calculation status: {data.get('status')}")
        print("TBS breakdown:", data.get('tbs_breakdown'))
        print("Comprehensive financials:", data.get('comprehensive_financials'))
        assert data.get('status') == 'success'
    except Exception as e:
        print(f"Error GET /api/pricing/tbs-calculation: {e}")

    # 5. Test BigQuery Manager and Dynamic Table Endpoints
    print("\nTesting BigQuery Manager & Multi-table Endpoints...")
    try:
        req = urllib.request.urlopen(f"{base_url}/bigquery-manager")
        assert req.status == 200
        print("GET /bigquery-manager status: 200")
        
        tables = ['dossiers', 'spatial_telemetry', 'inspection_evidence', 'simulations', 'audit_logs']
        for tbl in tables:
            req = urllib.request.urlopen(f"{base_url}/api/bq/table/{tbl}")
            data = json.loads(req.read().decode('utf-8'))
            assert data.get('status') == 'success'
            print(f"GET /api/bq/table/{tbl} -> status: {data.get('status')}, source: {data.get('source')}, rows: {len(data.get('rows', []))}")
    except Exception as e:
        print(f"Error testing BigQuery endpoints: {e}")

if __name__ == '__main__':
    test_endpoints()

