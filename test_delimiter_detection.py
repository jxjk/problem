#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试CSV分隔符检测函数的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from csv_import import _detect_csv_delimiter


def test_delimiter_detection():
    """测试各种CSV格式的分隔符检测"""
    
    print("开始测试CSV分隔符检测算法...")
    
    # 测试用例1: 标准逗号分隔
    csv_data1 = """title,description,equipment_type,phase
电机过热,电机温度过高,机械设备,usage
软件响应慢,系统响应时间长,软件系统,development"""
    
    delimiter1 = _detect_csv_delimiter(csv_data1)
    print(f"测试1 - 逗号分隔CSV: 检测到分隔符: '{repr(delimiter1)}' (预期: ',')")
    
    # 测试用例2: 分号分隔
    csv_data2 = """title;description;equipment_type;phase
电机过热;电机温度过高;机械设备;usage
软件响应慢;系统响应时间长;软件系统;development"""
    
    delimiter2 = _detect_csv_delimiter(csv_data2)
    print(f"测试2 - 分号分隔CSV: 检测到分隔符: '{repr(delimiter2)}' (预期: ';')")
    
    # 测试用例3: 制表符分隔
    csv_data3 = """title		description		equipment_type		phase
电机过热		电机温度过高		机械设备		usage
软件响应慢		系统响应时间长		软件系统		development"""
    
    delimiter3 = _detect_csv_delimiter(csv_data3)
    print(f"测试3 - 制表符分隔CSV: 检测到分隔符: '{repr(delimiter3)}' (预期: '\t')")
    
    # 测试用例4: 管道符分隔
    csv_data4 = """title|description|equipment_type|phase
电机过热|电机温度过高|机械设备|usage
软件响应慢|系统响应时间长|软件系统|development"""
    
    delimiter4 = _detect_csv_delimiter(csv_data4)
    print(f"测试4 - 管道符分隔CSV: 检测到分隔符: '{repr(delimiter4)}' (预期: '|')")
    
    # 测试用例5: 从sample1.csv提取的片段
    csv_data5 = """title,description,equipment_type,phase,discovered_by,discovered_at
电机过热问题,电机运行时温度过高，可能导致设备停机,机械设备,usage,张三,2024/1/15
软件响应缓慢,系统在处理大量数据时响应时间过长,软件系统,development,李四,2024/2/20
连接器接触不良,设备连接器经常出现接触问题，导致信号中断,电子设备,usage,王五,2024/3/10"""
    
    delimiter5 = _detect_csv_delimiter(csv_data5)
    print(f"测试5 - sample1.csv片段: 检测到分隔符: '{repr(delimiter5)}' (预期: ',')")
    
    # 测试用例6: 空数据
    csv_data6 = ""
    delimiter6 = _detect_csv_delimiter(csv_data6)
    print(f"测试6 - 空数据: 检测到分隔符: '{repr(delimiter6)}' (预期: None)")
    
    # 测试用例7: 只有一行
    csv_data7 = "title,description,equipment_type,phase"
    delimiter7 = _detect_csv_delimiter(csv_data7)
    print(f"测试7 - 单行数据: 检测到分隔符: '{repr(delimiter7)}' (预期: ',')")
    
    # 测试用例8: 不一致分隔符（错误数据）
    csv_data8 = """title,description,equipment_type
电机过热;电机温度过高,机械设备
软件响应慢,系统响应时间长;软件系统"""
    
    delimiter8 = _detect_csv_delimiter(csv_data8)
    print(f"测试8 - 不一致分隔符: 检测到分隔符: '{repr(delimiter8)}'")
    
    print("\n分隔符检测测试完成！")


if __name__ == "__main__":
    test_delimiter_detection()