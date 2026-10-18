import os

for p in ['templates/mobile.html', 'mobile/index.html']:
    if os.path.exists(p):
        lines = open(p, encoding='utf-8', errors='ignore').readlines()
        for i, l in enumerate(lines, 1):
            if any(k in l.lower() for k in ['capture', 'type="file"', "type='file'", 'camera_input', 'fileinput']):
                print(f"{p}:{i}: {l.strip()[:100]}")
