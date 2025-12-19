#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试sample1.csv文件的分隔符检测
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from csv_import import _detect_csv_delimiter

def test_sample1_csv():
    """测试sample1.csv文件的分隔符检测"""
    
    # 读取sample1.csv文件的前几行进行测试
    csv_file_path = "testcsv/sample1.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"文件不存在: {csv_file_path}")
        return
    
    # 尝试不同的编码格式读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
    file_content = None
    
    for encoding in encodings:
        try:
            with open(csv_file_path, 'r', encoding=encoding) as file:
                # 读取前1024字节用于检测CSV格式
                sample = file.read(1024)
                file_content = sample
                print(f"成功使用编码 {encoding} 读取文件")
                break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        print("无法识别CSV文件编码")
        return
    
    print(f"文件内容前200字符: {repr(file_content[:200])}")
    
    # 检测分隔符
    delimiter = _detect_csv_delimiter(file_content)
    print(f"检测到的分隔符: {repr(delimiter)}")
    
    if delimiter:
        print(f"使用分隔符 '{delimiter}' 解析前几行:")
        
        # 使用检测到的分隔符解析前几行
        import csv
        from io import StringIO
        file_io = StringIO(file_content)
        reader = csv.DictReader(file_io, delimiter=delimiter)
        
        # 读取前3行数据
        for i, row in enumerate(reader):
            if i >= 3:  # 只显示前3行
                break
            print(f"  第{i+1}行: {dict(list(row.items())[:3])}")  # 只显示前3个字段
    else:
        print("无法检测到分隔符")


if __name__ == "__main__":
    test_sample1_csv()