"""Simple fix - find lines ending with 'print(f"' or 'print("' and merge with next"""

with open('cli/controller.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
fixed_count = 0

while i < len(lines):
    line = lines[i]
    stripped = line.rstrip()
    
    # Check for broken print at end of line
    if (stripped.endswith('print(f"') or stripped.endswith('print("')):
        # Broken - merge with next line
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Merge: current + \n + next + close quote
            fixed = stripped + '\\n' + next_line + '\n'
            fixed_lines.append(fixed)
            fixed_count += 1
            i += 2
            continue
    
    # Check for lines with unclosed quotes in print
    elif 'print(' in line and line.count('"') % 2 == 1 and not stripped.endswith(')'):
        # Has odd number of quotes and doesn't end with )
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Merge
            fixed = stripped + '\\n' + next_line + '\n'
            fixed_lines.append(fixed)
            fixed_count += 1
            i += 2
            continue
    
    # Keep as-is
    fixed_lines.append(line)
    i += 1

print(f"Fixed {fixed_count} statements")

# Write
with open('cli/controller.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

# Test
import py_compile
try:
    py_compile.compile('cli/controller.py', doraise=True)
    print("✅ SUCCESS! File compiles!")
    print("\n🎉 RUN: python main.py --interactive")
except SyntaxError as e:
    print(f"⚠️  Error line {e.lineno}: {e.msg}")
