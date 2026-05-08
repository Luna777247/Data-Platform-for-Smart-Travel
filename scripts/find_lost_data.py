import os

count = 0
for root, dirs, files in os.walk('.'):
    if 'node_modules' in root or '.git' in root or '.gemini' in root:
        continue
    for f in files:
        if f.endswith('.json'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                    if 'google_raw' in content:
                        count += 1
                        if count % 100 == 0:
                            print(f"Found {count} files so far...")
            except:
                continue

print(f"Total Google Raw files found: {count}")
