"""
CSV导入功能单元测试
验证改进后的CSV导入功能
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from config import Config
from models import db, Problem, EquipmentType, ImportHistory
from csv_import import import_csv_file, validate_csv_headers, _sanitize_input
from app import app as flask_app


class TestCSVImport(unittest.TestCase):
    """CSV导入功能测试类"""

    def setUp(self):
        """测试前准备"""
        self.app = flask_app
        self.app.config.from_object(Config)
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
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

    def test_import_csv_success(self):
        """测试成功导入CSV文件"""
        csv_content = """title,description,equipment_type,phase,discovered_by,discovered_at
测试问题1,这是测试描述1,设备A,design,测试员1,2023-01-01
测试问题2,这是测试描述2,设备B,development,测试员2,2023-02-01
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = import_csv_file(csv_file_path)
            self.assertEqual(result['message'], 'CSV文件导入成功')
            self.assertEqual(result['importedCount'], 2)
            self.assertEqual(result['totalCount'], 2)
            self.assertIn('historyId', result)
            self.assertIn('processingTime', result)

            # 检查数据库中的记录
            problems = Problem.query.all()
            self.assertEqual(len(problems), 2)
            self.assertEqual(problems[0].title, '测试问题1')
            self.assertEqual(problems[0].description, '这是测试描述1')
            self.assertEqual(problems[1].title, '测试问题2')
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_with_chinese_headers(self):
        """测试中文列头的CSV文件导入"""
        csv_content = """标题,描述,设备类型,阶段,发现者,发现时间
测试问题3,这是测试描述3,设备C,usage,测试员3,2023-03-01
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = import_csv_file(csv_file_path)
            self.assertEqual(result['importedCount'], 1)
            self.assertEqual(result['totalCount'], 1)

            problems = Problem.query.all()
            self.assertEqual(len(problems), 1)
            self.assertEqual(problems[0].title, '测试问题3')
            self.assertEqual(problems[0].description, '这是测试描述3')
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_empty_file(self):
        """测试空CSV文件导入"""
        csv_content = """title,description
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = import_csv_file(csv_file_path)
            self.assertEqual(result['message'], 'CSV文件为空')
            self.assertEqual(result['importedCount'], 0)
            self.assertEqual(result['totalCount'], 0)
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_invalid_format(self):
        """测试无效格式的CSV文件"""
        csv_content = """invalid,format,content
without,proper,headers
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = import_csv_file(csv_file_path)
            # 即使格式无效，如果标题和描述字段都缺失，应该跳过所有行
            self.assertEqual(result['importedCount'], 0)
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_with_missing_optional_fields(self):
        """测试包含可选字段缺失的CSV文件"""
        csv_content = """title,description
测试问题4,这是测试描述4
测试问题5,这是测试描述5
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = import_csv_file(csv_file_path)
            self.assertEqual(result['importedCount'], 2)
            self.assertEqual(result['totalCount'], 2)

            problems = Problem.query.all()
            self.assertEqual(len(problems), 2)
            # 验证默认值
            for problem in problems:
                self.assertEqual(problem.phase, 'design')  # 默认阶段
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_with_malformed_dates(self):
        """测试包含格式错误日期的CSV文件"""
        csv_content = """title,description,discovered_at
测试问题6,这是测试描述6,invalid_date
测试问题7,这是测试描述7,2023-13-40
测试问题8,这是测试描述8,2023-05-15
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = import_csv_file(csv_file_path)
            self.assertEqual(result['importedCount'], 3)
            self.assertEqual(result['totalCount'], 3)

            problems = Problem.query.all()
            # 日期格式错误的应该被设置为None
            self.assertIsNone(problems[0].discovered_at)
            self.assertIsNone(problems[1].discovered_at)
            self.assertIsNotNone(problems[2].discovered_at)
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_large_file_size(self):
        """测试大文件导入限制"""
        # 创建超过限制的文件内容
        csv_content = "title,description\n"
        for i in range(105):  # 超过我们设置的100行限制
            csv_content += f"测试问题{i},这是测试描述{i}\n"

        csv_file_path = self.create_test_csv(csv_content)

        try:
            # 临时修改配置以测试限制
            from config import Config
            original_max_rows = Config.CSV_MAX_ROWS
            Config.CSV_MAX_ROWS = 100  # 设置为小的限制值

            result = import_csv_file(csv_file_path)
            # 应该只处理限制内的行数
            self.assertLessEqual(result['importedCount'], 100)
            self.assertLessEqual(result['totalCount'], 101)  # 总行数包括标题行，所以是101

            Config.CSV_MAX_ROWS = original_max_rows  # 恢复原始值
        finally:
            os.unlink(csv_file_path)

    def test_validate_csv_headers_valid(self):
        """测试有效的CSV文件头验证"""
        csv_content = """title,description,equipment_type,phase
测试,描述,设备,阶段
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = validate_csv_headers(csv_file_path)
            self.assertTrue(result['valid'])
            self.assertEqual(result['message'], 'CSV文件格式验证通过')
            self.assertIn('title', result['headers'])
            self.assertIn('description', result['headers'])
        finally:
            os.unlink(csv_file_path)

    def test_validate_csv_headers_invalid(self):
        """测试无效的CSV文件头验证"""
        csv_content = """col1,col2,col3
value1,value2,value3
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            result = validate_csv_headers(csv_file_path)
            self.assertFalse(result['valid'])
            self.assertIn('缺少必需的列', result['message'])
        finally:
            os.unlink(csv_file_path)

    def test_sanitize_input(self):
        """测试输入清理功能"""
        # 测试正常输入
        self.assertEqual(_sanitize_input('正常输入'), '正常输入')
        self.assertEqual(_sanitize_input(''), '')
        self.assertIsNone(_sanitize_input(None))

        # 测试包含恶意脚本的输入
        malicious_input = '<script>alert("xss")</script>正常文本'
        sanitized = _sanitize_input(malicious_input)
        self.assertNotIn('<script>', sanitized)
        self.assertIn('正常文本', sanitized)

        # 测试包含其他恶意标签的输入
        malicious_input2 = '<iframe src="javascript:alert(1)"></iframe>安全文本'
        sanitized2 = _sanitize_input(malicious_input2)
        self.assertNotIn('<iframe', sanitized2.lower())
        self.assertIn('安全文本', sanitized2)

    def test_import_csv_with_ai_analysis_error(self):
        """测试AI分析失败时的处理"""
        csv_content = """title,description
AI测试问题,AI测试描述
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            # 模拟AI分析失败
            with patch('csv_import.analyze_problem_with_ai', side_effect=Exception('AI分析失败')):
                result = import_csv_file(csv_file_path)
                self.assertEqual(result['importedCount'], 1)
                self.assertEqual(result['totalCount'], 1)

                # 检查问题是否仍然被创建，但AI分析字段为空
                problem = Problem.query.first()
                self.assertEqual(problem.title, 'AI测试问题')
                self.assertFalse(problem.ai_analyzed)
                self.assertIsNone(problem.ai_analysis)
        finally:
            os.unlink(csv_file_path)

    def test_import_csv_with_database_error(self):
        """测试数据库错误处理"""
        csv_content = """title,description
测试问题9,测试描述9
"""
        csv_file_path = self.create_test_csv(csv_content)

        try:
            # 模拟数据库错误
            with patch('csv_import.db.session.commit', side_effect=Exception('数据库错误')):
                with self.assertRaises(Exception):
                    import_csv_file(csv_file_path)
        finally:
            os.unlink(csv_file_path)


class TestCSVImportAppIntegration(unittest.TestCase):
    """CSV导入功能集成测试"""

    def setUp(self):
        """测试前准备"""
        self.app = flask_app
        self.app.config.from_object(Config)
        self.app.config['TESTING'] = True
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

    def test_csv_upload_endpoint(self):
        """测试CSV上传端点"""
        csv_content = """title,description,equipment_type
集成测试问题,集成测试描述,集成设备
"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as f:
            f.write(csv_content)
            csv_file_path = f.name

        try:
            with open(csv_file_path, 'rb') as f:
                response = self.client.post('/api/import-csv', 
                                            data={'csvFile': (f, 'test.csv')},
                                            content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['importedCount'], 1)
            self.assertIn('processing_time', data)
        finally:
            os.unlink(csv_file_path)

    def test_csv_upload_invalid_file_type(self):
        """测试上传非CSV文件"""
        txt_content = "这不是CSV文件内容"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write(txt_content)
            txt_file_path = f.name

        try:
            with open(txt_file_path, 'rb') as f:
                response = self.client.post('/api/import-csv', 
                                            data={'csvFile': (f, 'test.txt')},
                                            content_type='multipart/form-data')
            
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertIn('error', data)
        finally:
            os.unlink(txt_file_path)

    def test_csv_upload_no_file(self):
        """测试没有文件的上传请求"""
        response = self.client.post('/api/import-csv', 
                                    data={},
                                    content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], '请上传CSV文件')


if __name__ == '__main__':
    unittest.main()