#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to find all occurrences of the problematic string in ai_analysis.py file
"""

import re

def find_problematic_strings():
    """Find all occurrences of the problematic string pattern"""
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all return statements that contain the problematic string
    # Looking for: return "text with literal newlines"
    # This pattern looks for return statements that span multiple lines
    pattern = r'return ".*?基于历史数据分析.*?查询.*?设计建议.*?"'
    matches = re.findall(pattern, content, re.DOTALL)

    print(f'Found {len(matches)} matches:')
    for i, match in enumerate(matches):
        print(f'Match {i+1}:')
        print(repr(match))
        print()

    # Let's also look for the specific function to understand the context
    query_func_pattern = r'def _query_with_openai.*?def |$'
    # Just look for the function content specifically
    start_pos = content.find('def _query_with_openai')
    if start_pos != -1:
        # Find the end by looking for the next function definition or end of file
        next_def = content.find('\ndef ', start_pos + 1)
        if next_def == -1:
            next_def = len(content)
        func_content = content[start_pos:next_def]
        
        print("Content of _query_with_openai function:")
        print(repr(func_content[0:1000]))  # Print first 1000 chars

if __name__ == "__main__":
    find_problematic_strings()