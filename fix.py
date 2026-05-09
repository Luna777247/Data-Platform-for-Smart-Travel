with open('.gitignore', 'rb') as f:
    content = f.read()

content = content.replace(b'\x00', b'')

lines = content.decode('utf-8', errors='ignore').splitlines()
clean_lines = []
for line in lines:
    if line.strip() and not line.startswith('. b a c k u p'):
        clean_lines.append(line)

with open('.gitignore', 'w', encoding='utf-8') as f:
    for line in clean_lines:
        f.write(line + '\n')
    f.write('.backup_before_migration_20260509_051036/\n')
