import re
import os

html_path = r"C:\Users\timot\Documents\Programmation\Emulation_All_console\frontend\index.html"
js_path = r"C:\Users\timot\Documents\Programmation\Emulation_All_console\frontend\app.js"

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
js_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js))

missing = js_ids - html_ids
print("JS IDs count:", len(js_ids))
print("HTML IDs count:", len(html_ids))
if missing:
    print("MISSING IDs in HTML:", missing)
else:
    print("PASS: All JS IDs exist in HTML!")
