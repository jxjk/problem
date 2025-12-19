#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix the f-string concatenation issue in ai_analysis.py
"""

def fix_fstring_concatenation():
    """Fix the f-string concatenation issue in the file"""
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # From our earlier analysis, we know the exact line that has the issue
    # It's in the get_design_suggestions_for_query function, in an exception handler
    import ast  # We'll use a literal replacement approach
    
    # Define the old and new strings exactly as they appear
    old_text = "return f\"针对您的查询 '{{' + query_text + '}}'，建议在设计时考虑以下几个方面：\\n\\n1. 材料选择的可靠性\\n2. 环境适应性设计\\n3. 维护便利性\"".replace('{{', '{\' + query_text + \'').replace('}}', '}')  # Actually this is wrong approach
    
    # Let me get it right based on exact line from earlier analysis:
    old_string = '''return f"针对您的查询 '{' + query_text + '}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性"'''
    
    new_string = '''return f"针对您的查询 '{query_text}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性"'''

    # Since direct string replacement didn't work, let me read the file and work with the exact bytes
    if old_string in content:
        print("Found and fixing the f-string concatenation issue")
        content_fixed = content.replace(old_string, new_string)
        
        with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
            f.write(content_fixed)
        
        print("Fixed the f-string concatenation issue")
    else:
        print("Could not find the exact pattern. Let me check the exact content again.")
        # Let's read the exact problematic section and fix it
        with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the problematic line
        for i, line in enumerate(lines):
            if "'{'" in line and "' + query_text + '" in line and "'}'" in line:
                print(f"Found problematic line at {i+1}: {repr(line)}")
                # Fix this specific line
                fixed_line = line.replace("'{\' + query_text + \'}'", "'{query_text}'")
                if fixed_line != line:
                    print(f"Fixed line to: {repr(fixed_line)}")
                    lines[i] = fixed_line
                    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    print("Applied fix to the problematic line")
                break

if __name__ == "__main__":
    fix_fstring_concatenation()
