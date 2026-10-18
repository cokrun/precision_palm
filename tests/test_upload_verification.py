import urllib.request
import json
import sqlite3
import os

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = []

filename = 'test_drone_flight_sample.jpg'
image_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x10\x00\x10\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'

body.append(f'--{boundary}'.encode())
body.append(f'Content-Disposition: form-data; name="photo"; filename="{filename}"'.encode())
body.append(b'Content-Type: image/jpeg\r\n')
body.append(image_bytes)

body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="id_kebun"\r\n')
body.append(b'1')

body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="kode_kebun"\r\n')
body.append(b'EST-MDN-001')

body.append(f'--{boundary}'.encode())
body.append(b'Content-Disposition: form-data; name="title"\r\n')
body.append(b'Test UAV Drone Canopy Flight')

body.append(f'--{boundary}--\r\n'.encode())

payload = b'\r\n'.join(body)

req = urllib.request.Request(
    'http://127.0.0.1:8080/api/spatial/upload-photo',
    data=payload,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}'
    }
)

resp = urllib.request.urlopen(req)
res_data = json.loads(resp.read().decode('utf-8'))
print('UPLOAD RESPONSE STATUS:', resp.status)
print('UPLOAD SUCCESS:', res_data.get('success'))
print('EVIDENCE ID:', res_data.get('evidence_id'))
print('FILE URL:', res_data.get('file_url'))
print('FILENAME:', res_data.get('filename'))

ev_id = res_data.get('evidence_id')
file_url = res_data.get('file_url')

# Test read back image
get_req = urllib.request.urlopen(f'http://127.0.0.1:8080{file_url}')
retrieved_bytes = get_req.read()
print('READ BACK HTTP STATUS:', get_req.status)
print('READ BACK CONTENT TYPE:', get_req.headers.get('Content-Type'))
print('READ BACK SIZE (BYTES):', len(retrieved_bytes))
print('BYTES MATCH:', retrieved_bytes == image_bytes)

# Check SQLite database
conn = sqlite3.connect('precision_palm.db')
cursor = conn.cursor()
cursor.execute('SELECT evidence_id, dossier_id, perspective_mode, file_size_bytes FROM inspection_evidence WHERE evidence_id = ?', (ev_id,))
row = cursor.fetchone()
print('DATABASE RECORD VERIFICATION:', row)
conn.close()
