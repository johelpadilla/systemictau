import re

with open('src/systemictau/desktop/app.py', 'r') as f:
    content = f.read()

# Replace pady=(15, 0) -> pady=(2, 0)
content = re.sub(r'pady=\(15,\s*0\)', 'pady=(2, 0)', content)
# Replace pady=(10, 0) -> pady=(2, 0)
content = re.sub(r'pady=\(10,\s*0\)', 'pady=(2, 0)', content)
# Replace pady=(5, 0) -> pady=(2, 0)
content = re.sub(r'pady=\(5,\s*0\)', 'pady=(2, 0)', content)
# Replace pady=(0, 5) -> pady=(0, 2)
content = re.sub(r'pady=\(0,\s*5\)', 'pady=(0, 2)', content)
# Replace pady=(0, 10) -> pady=(0, 5)
content = re.sub(r'pady=\(0,\s*10\)', 'pady=(0, 5)', content)
# Replace pady=(5, 5) -> pady=(2, 2)
content = re.sub(r'pady=\(5,\s*5\)', 'pady=(2, 2)', content)

# But wait, there are buttons that we want to keep some padding.
with open('src/systemictau/desktop/app.py', 'w') as f:
    f.write(content)
print("Paddings reduced")
