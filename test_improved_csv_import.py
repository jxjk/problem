"""
测试改进后的CSV导入功能
验证不合格记录分离处理、统计功能和错误严重程度区分等功能
"""
import os
import tempfile
import csv
from datetime import datetime
from models import db, Problem, EquipmentType, ImportHistory
from csv_import import import_csv_file, save_failed_records_to_csv, _is_fatal_error
from app import app


def test_improved_csv_import():
    """测试改进后的CSV导入功能"""
    with app.app_context():
        # 创建测试CSV文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['title', 'description', 'equipment_type', 'phase', 'priority', 'discovered_by', 'discovered_at'])
            # 写入有效数据
            writer.writerow(['设备故障1', '设备A在运行过程中出现异常', '设备A', 'usage', 'high', '张三', '2023-10-01'])
            writer.writerow(['设备故障2', '设备B在设计阶段存在问题', '设备B', 'design', 'medium', '李四', '2023-10-02'])
            # 写入无效数据（错误的阶段值）
            writer.writerow(['设备故障3', '设备C在测试阶段有问题', '设备C', 'invalid_phase', 'low', '王五', '2023-10-03'])
            # 写入另一个有效数据
            writer.writerow(['设备故障4', '设备D在维护阶段出现问题', '设备D', 'maintenance', 'critical', '赵六', '2023-10-04'])
            # 写入包含特殊字符过多的数据
            writer.writerow(['设备故障5', '设备E问题@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@', '设备E', 'development', 'high', '孙七', '2023-10-05'])
            
            test_csv_path = f.name

        try:
            # 执行改进后的CSV导入
            print("开始测试改进后的CSV导入功能...")
            result = import_csv_file(test_csv_path, fail_on_error=False)
            
            print(f"导入结果: {result}")
            print(f"总记录数: {result['totalCount']}")
            print(f"成功导入: {result['importedCount']}")
            print(f"失败记录: {result['failedCount']}")
            print(f"失败记录详情: {result.get('failedRecords', [])}")
            
            # 验证数据库中的数据
            all_problems = Problem.query.all()
            print(f"数据库中当前问题总数: {len(all_problems)}")
            
            # 验试错误严重程度判断
            print(f"测试错误严重程度判断...")
            print(f"普通错误是否为致命: {_is_fatal_error('第1行: 日期格式无效')}")
            print(f"致命错误是否为致命: {_is_fatal_error('数据库约束违反')}")
            
            # 测试保存失败记录功能
            if result.get('failedRecords'):
                failed_file_path = save_failed_records_to_csv(result['failedRecords'])
                print(f"失败记录已保存到: {failed_file_path}")
                
                # 验证失败记录文件
                with open(failed_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    failed_rows = list(reader)
                    print(f"失败记录文件中的行数: {len(failed_rows)}")
            
            # 清理测试数据
            for problem in all_problems:
                db.session.delete(problem)
            db.session.commit()
            
            print("测试完成！")
            
        finally:
            # 删除测试CSV文件
            os.unlink(test_csv_path)


def test_error_severity_detection():
    """测试错误严重程度检测功能"""
    print("测试错误严重程度判断功能:")
    
    test_cases = [
        ("第1行: 日期格式无效 '2023-13-01'", False),
        ("第2行: 数据库约束违反 - 外键不存在", True),
        ("第3行: 优先级值无效 'super_high'", False),
        ("第4行: 路径遍历攻击检测", True),
        ("第5行: 字段长度超出限制", False)
    ]
    
    for error_msg, expected in test_cases:
        result = _is_fatal_error(error_msg)
        status = "✓" if result == expected else "✗"
        print(f"{status} 错误: '{error_msg}' -> 致命: {result}, 期望: {expected}")


if __name__ == "__main__":
    test_error_severity_detection()
    print("\n" + "="*50 + "\n")
    test_improved_csv_import()