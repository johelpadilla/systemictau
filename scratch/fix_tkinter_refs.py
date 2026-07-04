import re

with open("src/systemictau/desktop/app.py", "r") as f:
    content = f.read()

# Remove 'import tkinter.messagebox'
content = re.sub(r'^[ \t]*import tkinter\.messagebox\n?', '', content, flags=re.MULTILINE)

# Replace 'tkinter.messagebox.' with 'messagebox.'
content = content.replace("tkinter.messagebox.", "messagebox.")

with open("src/systemictau/desktop/app.py", "w") as f:
    f.write(content)

print("Cleaned up tkinter.messagebox references.")
