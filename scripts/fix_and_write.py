import os, base64, sys
# Read the current write_dash.py, extract and fix HTML, write it
with open('D:/workplace/scripts/write_dash.py', 'r', encoding='utf-8') as f:
    content = f.read()
# Find the HTML triple-quoted string
start = content.find('html = """')
start = start + len('html = """')
end = content.rfind('"""')
html = content[start:end]
# Check for bad characters
bad_positions = []
for i, ch in enumerate(html):
    if 0xD800 <= ord(ch) <= 0xDFFF:
        bad_positions.append((i, ord(ch)))
if bad_positions:
    print(f"Found {len(bad_positions)} surrogates, replacing...")
    for pos, code in reversed(bad_positions):
        # Replace with space
        html = html[:pos] + ' ' + html[pos+1:]
# Write
with open('D:/workplace/app/static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written with {len(html)} chars")
