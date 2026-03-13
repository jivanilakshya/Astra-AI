"""Complete fix for all broken string literals"""
import re

# Read file
with open('cli/controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count fixes
fixes = 0

# Pattern 1: print(f"...\n  where newline is literal
# Replace: print(f"text\n with print(f"text\n"
while True:
    match = re.search(r'(print\(f?")(.*?)\n([^\"])', content, re.DOTALL)
    if not match:
        break
    
    # Check if this is an unterminated string
    quote_part = match.group(2)
    if quote_part.count('"') % 2 == 0:
        # Even number of quotes, string is terminated, not our issue
        # Move past this match
        start_pos = match.end()
        content_after = content[start_pos:]
        if content_after:
            content = content[:match.end()] + content_after
        break
    
    # Odd number of quotes, this is unterminated
   # Get the text up to the newline
    before = content[:match.start()]
    print_start = match.group(1)  # print(f" or print("
    text = match.group(2)  # The text before newline
    after_newline = match.group(3)  # Character after newline
    rest = content[match.start() + len(match.group(0)) - 1:]  # Rest from newline
    
    # Find where the actual line ends (look for the next line that doesn't start with special chars)
    lines = rest.split('\n')
    continued_text = lines[0].strip()
    
    # Reconstruct
    fixed = f'{print_start}{text}\\n{continued_text}"\n{lines[1] if len(lines) > 1 else ""}'
    
    content = before + fixed
    if len(lines) > 2:
        content += '\n'.join(lines[2:])
    
    fixes += 1
    if fixes > 50:  # Safety limit
        print("⚠️ Hit safety limit")
        break

print(f"Applied {fixes} automatic fixes")

# Now handle simple cases - print(" or print(f" at end of line
content = re.sub(r'print\("([^\n]*)\n([^\"])', r'print("\\n\1\n\2', content)
content = re.sub(r'print\(f"([^\n]*)\n([^\"])', r'print(f"\\n\1\n\2', content)

# Write back
with open('cli/controller.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed all patterns")

# Test  
import py_compile
try:
    py_compile.compile('cli/controller.py', doraise=True)
    print("✅ File compiles successfully!")
except SyntaxError as e:
    print(f"⚠️ Line {e.lineno}: {e.msg}")
