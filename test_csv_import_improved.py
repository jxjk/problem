"""
改进的CSV导入功能单元测试
验证添加枚举值验证、数据验证和改进分隔符检测后的功能
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from config import Config
from models import db, Problem, EquipmentType, ImportHistory, ProblemCategory, SolutionCategory
from csv_import import import_csv_file, validate_csv_headers, _sanitize_input, _validate_enum_value, _clean_and_validate_data, _detect_csv_delimiter
from app import app as flask_app


class TestImprovedCSVImport(unittest.TestCase):
    """改进的CSV导入功能测试类"""

    def setUp(self):
        """测试前准备"""
        self.app = flask_app
        self.app.config.from_object(Config)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def create_test_csv(self, content):
        """创建测试用CSV文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(content)
            return f.name

    def test_enum_validation(self):
        """测试枚举值验证功能"""
        # 测试有效的枚举值
        is_valid, error_msg = _validate_enum_value('design', ['design', 'development', 'usage', 'maintenance'], 'phase')
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        # 测试无效的枚举值
        is_valid, error_msg = _validate_enum_value('invalid', ['design', 'development', 'usage', 'maintenance'], 'phase')
        self.assertFalse(is_valid)
        self.assertIn('无效的枚举值', error_msg)
        self.assertIn('design', error_msg)

        # 测试大小写不敏感
        is_valid, error_msg = _validate_enum_value('DESIGN', ['design', 'development', 'usage', 'maintenance'], 'phase')
        self.assertTrue(is_valid)

        # 测试空值
        is_valid, error_msg = _validate_enum_value('', ['design', 'development', 'usage', 'maintenance'], 'phase')
        self.assertTrue(is_valid)

    def test_data_cleaning_and_validation(self):
        """测试数据清理和验证功能"""
        # 测试正常数据
        row_data = {
            'title': '测试问题',
            'description': '测试描述',
            'equipment_type': '设备A',
            'phase': 'design',
            'discovered_by': '测试员',
            'discovered_at': '2023-01-01',
            'priority': 'medium'
        }
        cleaned_data, errors = _clean_and_validate_data(row_data, 1)
        self.assertEqual(cleaned_data['title'], '测试问题')
        self.assertEqual(cleaned_data['phase'], 'design')
        self.assertEqual(cleaned_data['priority'], 'medium')
        self.assertEqual(len(errors), 0)

        # 测试无效的枚举值
        row_data['phase'] = 'invalid_phase'
        cleaned_data, errors = _clean_and_validate_data(row_data, 1)
        self.assertIn('无效的枚举值', errors[0])
        self.assertEqual(cleaned_data['phase'], 'design')  # 应该使用默认值

        # 测试XSS清理
        row_data['title'] = '<script>alert("xss")</script>安全标题'
        cleaned_data, errors = _clean_and_validate_data(row_data, 1)
        self.assertNotIn('<script>', cleaned_data['title'])
        self.assertIn('安全标题', cleaned_data['title'])

    def test_delimiter_detection_improvements(self):
        """测试改进的分隔符检测算法"""
        # 测试包含大量逗号的文本（应该不会被误识别为分隔符）
        csv_with_commas = """title|description|phase
问题1|"这是一个包含,很多,逗号,的描述文本,用来测试分隔符检测算法,确保它不会被大量逗号误导"|design
问题2|"另一个包含,逗号的,描述文本,应该正确处理"|usage"""
        delimiter = _detect_csv_delimiter(csv_with_commas)
        self.assertEqual(delimiter, '|', "应该检测到管道符作为分隔符，而不是逗号")

        # 测试标准CSV
        csv_standard = """title,description,phase
测试问题,测试描述,design"""
        delimiter = _detect_csv_delimiter(csv_standard)
        self.assertEqual(delimiter, ',', "应该检测到逗号作为分隔符")

    def test_import_csv_with_enum_validation(self):
        """测试包含枚举值验证的CSV导入"""
        csv_content = """title,description,equipment_type,phase,priority,discovered_by,discovered_at
测试问题1,这是测试描述1,设备A,design,high,测试员1,2023-01-01
测试问题2,这是测试描述2,设备B,invalid_phase,invalid_priority,测试员2,2023-02-01
测试问题3,这是测试描述3,设备C,usage,critical,测试员3,2023-03-01
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            with patch('csv_import.analyze_problem_with_ai', return_value={
                'analysis': '测试AI分析结果',
                'problem_category_id': 1,
                'solution_category_id': 1,
                'priority': 'medium'
            }):
                result = import_csv_file(csv_file_path)
                # 应该成功导入所有行（无效枚举值会被替换为默认值）
                self.assertGreater(result['importedCount'], 0)
                self.assertIn('errorCount', result)  # 新增的错误计数字段

                # 检查导入的问题
                problems = Problem.query.all()
                self.assertGreater(len(problems), 0)
                # 验证第二行的无效枚举值被处理
                for problem in problems:
                    self.assertIn(problem.phase, ['design', 'development', 'usage', 'maintenance'])
                    self.assertIn(problem.priority, ['low', 'medium', 'high', 'critical'])
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_with_xss_protection(self):
        """测试XSS保护功能"""
        csv_content = """title,description,equipment_type,phase
<script>alert('xss')</script>安全标题,"<script>alert('xss')</script>安全描述",设备A,design
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            with patch('csv_import.analyze_problem_with_ai', return_value={
                'analysis': '测试AI分析结果',
                'problem_category_id': 1,
                'solution_category_id': 1,
                'priority': 'medium'
            }):
                result = import_csv_file(csv_file_path)
                self.assertGreater(result['importedCount'], 0)

                # 检查导入的问题标题和描述是否被清理
                problem = Problem.query.first()
                self.assertNotIn('<script>', problem.title)
                self.assertNotIn('<script>', problem.description)
                self.assertIn('安全标题', problem.title)
                self.assertIn('安全描述', problem.description)
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_large_comma_text(self):
        """测试包含大量逗号的文本导入（验证改进的分隔符检测）"""
        csv_content = """title|description|equipment_type|phase
问题1|"这个描述包含,很多逗号,用来测试,分隔符检测,算法是否,会被大量,逗号误导,导致错误,解析数据"|设备A|design
问题2|"另一个包含,逗号的文本,用于验证,算法的准确性"|设备B|usage
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            with patch('csv_import.analyze_problem_with_ai', return_value={
                'analysis': '测试AI分析结果',
                'problem_category_id': 1,
                'solution_category_id': 1,
                'priority': 'medium'
            }):
                result = import_csv_file(csv_file_path)
                self.assertEqual(result['importedCount'], 2)

                # 检查导入的问题描述是否完整（包含所有逗号）
                problems = Problem.query.all()
                self.assertEqual(len(problems), 2)
                # 验证描述中的逗号没有被误处理
                self.assertIn(',', problems[0].description)
                self.assertIn(',', problems[1].description)
        finally:
            os.unlink(csv_file_path)

    def test_csv_validation_with_enum_check(self):
        """测试CSV验证功能（包含枚举值检查）"""
        csv_content = """title,description,phase,priority
测试问题,测试描述,design,medium
测试问题2,测试描述2,invalid_phase,high
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = validate_csv_headers(csv_file_path)
            # 应该仍然有效，但可能有警告
            self.assertTrue(result['valid'])
            self.assertIn('CSV文件格式验证通过', result['message'])
        finally:
            os.unlink(csv_file_path)

    def test_file_size_limit(self):
        """测试文件大小限制功能"""
        # 创建大文件内容
        large_content = "title,description\n"
        # 创建超过配置限制的文件
        for i in range(10000):  # 大文件
            large_content += f"问题{i},描述{i}\n"

        csv_file_path = self.create_test_csv(large_content)

        try:
            # 临时修改配置
            original_limit = getattr(Config, 'CSV_FILE_SIZE_LIMIT', 100 * 1024 * 1024)
            Config.CSV_FILE_SIZE_LIMIT = 1024  # 设置为1KB限制
            
            with self.assertRaises(ValueError) as context:
                import_csv_file(csv_file_path)
            self.assertIn('文件大小超过限制', str(context.exception))
            
            # 恢复原始设置
            Config.CSV_FILE_SIZE_LIMIT = original_limit
        finally:
            os.unlink(csv_file_path)

    def test_row_limit(self):
        """测试行数限制功能"""
        # 创建超过行数限制的文件内容
        csv_content = "title,description\n"
        for i in range(150):  # 超过默认100行限制
            csv_content += f"问题{i},描述{i}\n"

        csv_file_path = self.create_test_csv(csv_content)

        try:
            # 临时修改配置以测试限制
            original_max_rows = getattr(Config, 'CSV_MAX_ROWS', 10000)
            Config.CSV_MAX_ROWS = 100  # 设置为小的限制值

            result = import_csv_file(csv_file_path)
            # 应该只处理限制内的行数
            self.assertLessEqual(result['totalCount'], 101)  # 总行数包括标题行
            self.assertLessEqual(result['importedCount'], 100)

            Config.CSV_MAX_ROWS = original_max_rows  # 恢复原始值
        finally:
            os.unlink(csv_file_path)

    def test_invalid_file_path_security(self):
        """测试文件路径安全性"""
        # 测试路径遍历攻击
        with self.assertRaises(ValueError) as context:
            import_csv_file('../../secret_file.txt')
        self.assertIn('非法文件路径', str(context.exception))

        # 测试绝对路径
        with self.assertRaises(ValueError) as context:
            import_csv_file('/etc/passwd')
        self.assertIn('非法文件路径', str(context.exception))


class TestCSVImportIntegration(unittest.TestCase):
    """CSV导入功能集成测试"""

    def setUp(self):
        """测试前准备"""
        self.app = flask_app
        self.app.config.from_object(Config)
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.ctx = self.app.app_context()
        self.ctx.push()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """测试后清理"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.ctx.pop()

    def test_csv_validation_endpoint(self):
        """测试CSV验证端点"""        
        # 在测试中，我们测试验证函数本身
        csv_content = """title,description,equipment_type,phase,priority
测试问题,测试描述,设备A,design,medium
测试问题2,测试描述2,设备B,usage,high
"""
        csv_file_path = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8').name
        with open(csv_file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)

        try:
            result = validate_csv_headers(csv_file_path)
            self.assertTrue(result['valid'])
            self.assertIn('CSV文件格式验证通过', result['message'])
            self.assertIn('title', result['headers'])
            self.assertIn('description', result['headers'])
        finally:
            os.unlink(csv_file_path)


if __name__ == '__main__':
    unittest.main()