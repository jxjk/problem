#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix the specific syntax error in ai_analysis.py file
"""

def fix_specific_syntax_error():
    """Fix the specific unterminated string literal in ai_analysis.py"""
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # The problematic string - this one still has literal newlines
    # It's specifically the one in the "except Exception as e:" block
    old_string = '''        return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"'''

    # Fixed version with proper escaped newlines
    new_string = '''        return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"'''

    print("Looking for the problematic string...")
    print("Old string (repr):", repr(old_string))
    print()
    
    if old_string in content:
        print("Found the exact problematic string!")
        content_fixed = content.replace(old_string, new_string)

        # Write the fixed content back to the file
        with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
            f.write(content_fixed)

        print('File has been fixed.')
    else:
        print("Could not find the exact problematic string.")
        print("Let me try to find what's actually in the file...")

if __name__ == "__main__":
    fix_specific_syntax_error()