import os
import json

root_dir = r"D:\Data-Platform-for-Smart-Travel"
json_list = r"D:\Data-Platform-for-Smart-Travel\json_files.txt"

stats = {}

with open(json_list, mode='r', encoding='utf-16') as f:
    for line in f:
        path = line.strip()
        if "storage" in path.lower():
            # Get relative path from root
            rel = os.path.relpath(os.path.dirname(path), root_dir)
            stats[rel] = stats.get(rel, 0) + 1

print(f"{'Count':<10} | {'Directory'}")
print("-" * 50)
for d, c in sorted(stats.items(), key=lambda x: x[0]):
    print(f"{c:<10} | {d}")
