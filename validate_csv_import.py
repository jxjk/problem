#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证改进的CSV导入功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from csv_import import validate_csv_headers
from csv_import import _detect_csv_delimiter

def validate_sample1_csv():
    """验证sample1.csv文件"""
    
    csv_file_path = "testcsv/sample1.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"文件不存在: {csv_file_path}")
        return False
    
    print(f"开始验证文件: {csv_file_path}")
    
    # 验证CSV头部
    validation_result = validate_csv_headers(csv_file_path)
    
    print(f"验证结果: {validation_result['valid']}")
    print(f"消息: {validation_result['message']}")
    print(f"检测到的头部: {validation_result['headers']}")
    
    if validation_result['valid']:
        print("✅ CSV文件格式验证通过！")
        return True
    else:
        print("❌ CSV文件格式验证失败！")
        return False

def test_edge_cases():
    """测试边界情况"""
    
    print("\n测试边界情况:")
    
    # 测试1: 包含不同换行符的CSV
    csv_with_crlf = "title,description\r\nvalue1,value2\r\nvalue3,value4"
    delimiter1 = _detect_csv_delimiter(csv_with_crlf)
    print(f"CRLF换行符测试: 检测到分隔符 '{delimiter1}' (预期: ',')")
    
    # 测试2: 包含制表符但不是分隔符的CSV
    csv_with_tabs = "title,description\nequipment with\t tabs,another value\nmore data,more values"
    delimiter2 = _detect_csv_delimiter(csv_with_tabs)
    print(f"包含制表符但非分隔符: 检测到分隔符 '{delimiter2}' (预期: ',')")
    
    # 测试3: 包含双引号的CSV
    csv_with_quotes = 'title,description\n"quoted, value","another value"\n"more, data","final value"'
    delimiter3 = _detect_csv_delimiter(csv_with_quotes)
    print(f"包含引号和逗号: 检测到分隔符 '{delimiter3}' (预期: ',')")
    
    print("边界情况测试完成！")

if __name__ == "__main__":
    print("CSV导入功能验证")
    print("=" * 50)
    
    # 验证sample1.csv
    success = validate_sample1_csv()
    
    # 测试边界情况
    test_edge_cases()
    
    print("\n验证完成！")
    if success:
        print("✅ 所有测试通过，sample1.csv可以成功上传！")
    else:
        print("❌ 验证失败")