#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix syntax error in ai_analysis.py file
"""

def fix_ai_analysis_file():
    """Fix the unterminated string literal in ai_analysis.py"""
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace the problematic multi-line string with properly escaped version
    # Original string that spans multiple lines and causes syntax error
    old_string = '''return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"'''

    # Fixed version with proper escaped newlines
    new_string = '''return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"'''

    content_fixed = content.replace(old_string, new_string)

    # Write the fixed content back to the file
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
        f.write(content_fixed)

    print('File has been fixed. Check for syntax errors.')

if __name__ == "__main__":
    fix_ai_analysis_file()