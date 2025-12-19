#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Final script to fix all multi-line string literals in ai_analysis.py
"""

def fix_all_multiline_strings():
    """Fix all multi-line string literals in the file"""
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace all problematic multi-line strings
    # Pattern: return "text with literal newlines" 
    import re
    
    # Find all return statements with multi-line string literals
    # This looks for strings that span multiple lines
    pattern = r'(return\s+)"([^"]*)"'
    
    # We need to find strings that have actual newline characters inside them
    def fix_multiline_string(match):
        prefix = match.group(1)  # the "return " part
        string_content = match.group(2)  # the string content
        
        # Check if the string content contains actual newlines
        if '\n' in string_content:
            # Escape the newlines
            fixed_content = string_content.replace('\n', '\\n')
            return f'{prefix}"{fixed_content}"'
        else:
            # No newlines, return original
            return match.group(0)
    
    # Apply the fix to all problematic strings
    fixed_content = re.sub(pattern, fix_multiline_string, content)
    
    # Write the fixed content back
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print('Applied fixes to all multi-line string literals.')
    
    # Also manually fix the specific known problematic strings
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the specific problematic strings with proper escaping
    fixes_applied = 0
    
    # Look for the exact pattern that has literal newlines
    problematic_patterns = [
        'return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"'
    ]
    
    for pattern in problematic_patterns:
        if pattern in content:
            fixed_pattern = 'return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\\n\\n1. 在设计阶段应特别注意材料选择\\n2. 建议增加冗余设计提高可靠性\\n3. 考虑环境因素对设备的影响"'
            content = content.replace(pattern, fixed_pattern)
            fixes_applied += 1
    
    if fixes_applied > 0:
        with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Applied {fixes_applied} specific fixes.')
    
    print('All fixes applied.')

if __name__ == "__main__":
    fix_all_multiline_strings()