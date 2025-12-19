#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix the f-string concatenation issue in ai_analysis.py
"""

def fix_fstring_concatenation():
    """Fix the f-string concatenation issue in the file"""
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The problematic pattern: f-string mixed with string concatenation
    old_pattern = "f\"针对您的查询 '{{' + query_text + '}}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性\""
    
    # Replace with proper f-string syntax
    # Need to match the exact string that was found
    old_string = '''return f"针对您的查询 '{' + query_text + '}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性"'''
    
    new_string = '''return f"针对您的查询 '{query_text}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性"'''

    if old_string in content:
        print("Found the f-string concatenation issue")
        content_fixed = content.replace(old_string, new_string)
        
        with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
            f.write(content_fixed)
        
        print("Fixed the f-string concatenation issue")
    else:
        print("Could not find the exact f-string concatenation pattern")
        # Let's try to find what's actually there
        import re
        # Look for the exact pattern with the mixed f-string and concatenation
        pattern = r'return f"针对您的查询 \''{''.*?\+ query_text \+.*?'\'，建议在设计时考虑以下几个方面：'
        matches = re.findall(pattern, content)
        print(f"Found {len(matches)} matches with the pattern")

if __name__ == "__main__":
    fix_fstring_concatenation()