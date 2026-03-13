"""Fix all broken print statements line by line"""

with open('cli/controller.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
fixed_count = 0

while i < len(lines):
    line = lines[i]
    
    # Check if this is a print statement with unclosed quote
    if ('print(' in line) and ('"' in line):
        # Count quotes
        quotes = line.count('"')
        
        # Check if quotes are balanced (accounting for escape sequences)
        # Simple heuristic: if line ends with \n and no closing paren with quote before it
        stripped = line.rstrip()
        
        # Pattern: print(f"text or print("text with no closing
        if (stripped.endswith('print(f"') or stripped.endswith('print("') or 
            ('"' in stripped and not (stripped.endswith('")') or stripped.endswith('")'))):
            
            # This line has unclosed string - need to merge with next line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_content = next_line.strip()
                
                # Merge: add \n + next line content + closing quote
                current = line.rstrip()
                
                # Build fixed line
                fixed = current + '\\n' + next_content
                if not fixed.endswith('"'):
                    fixed += '"'
                fixed += '\n'
                
                fixed_lines.append(fixed)
                fixed_count += 1
                i += 2  # Skip next line as it's been merged
                continue
    
    # Normal line, keep as is
    fixed_lines.append(line)
    i += 1

print(f"Fixed {fixed_count} broken print statements")

# Write back
with open('cli/controller.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

# Verify
import py_compile
try:
    py_compile.compile('cli/controller.py', doraise=True)
    print("✅ File compiles successfully!")
    print("\n🎉 NOW RUN: python main.py --interactive")
except SyntaxError as e:
    print(f"⚠️  Still has error at line {e.lineno}")
    print(f"    {e.msg}")
    # Show the problematic line
    with open('cli/controller.py', 'r') as f:
        file_lines = f.readlines()
        if e.lineno <= len(file_lines):
            print(f"    Line: {file_lines[e.lineno-1].strip()}")
