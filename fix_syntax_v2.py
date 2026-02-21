"""Comprehensive syntax fix for controller.py"""

# Read the file
with open('cli/controller.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Check if this is a broken print(" line
    if line.strip().startswith('print("') and line.strip() == 'print("':
        # This is a broken line - the string continues on next line
        # Reconstruct it
        next_line = lines[i+1] if i+1 < len(lines) else ""
        # Combine them: print("content")
        content = next_line.strip()
        indent = line[:len(line) - len(line.lstrip())]
        fixed_lines.append(f'{indent}print("\\n{content}')
        i += 2  # Skip next line
    else:
        fixed_lines.append(line)
        i += 1

# Write back
with open('cli/controller.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✓ Fixed all broken print statements!")
print("Verifying...")

# Try to compile
import py_compile
try:
    py_compile.compile('cli/controller.py', doraise=True)
    print("✓ File compiles successfully!")
except SyntaxError as e:
    print(f"❌ Still has error: {e}")
    print(f"   Line {e.lineno}: {e.text}")
