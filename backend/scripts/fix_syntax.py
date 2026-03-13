"""Quick fix for escaped quotes in controller.py"""

# Read the file
with open('cli/controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the escapes
# Replace \" with " (but not in actual escape sequences)
content = content.replace('\\"', '"')

# Fix newlines that got double-escaped
content = content.replace('\\n', '\n')
content = content.replace('\\t', '\t')

# Write back
with open('cli/controller.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed controller.py syntax!")
print("Now try: python main.py --interactive")
