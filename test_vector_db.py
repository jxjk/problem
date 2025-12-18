"""
向量数据库单元测试
"""
import unittest
import tempfile
import os
from vector_db import VectorDB, VectorDBException
from config import Config


class TestVectorDB(unittest.TestCase):
    """向量数据库测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        # 临时修改配置
        self.original_persist_dir = Config.VECTOR_DB_PERSIST_DIR
        Config.VECTOR_DB_PERSIST_DIR = self.temp_dir
        
        # 创建向量数据库实例
        self.vector_db = VectorDB()
    
    def tearDown(self):
        """测试后清理"""
        # 恢复原始配置
        Config.VECTOR_DB_PERSIST_DIR = self.original_persist_dir
        
        # 清理临时目录
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_problem(self):
        """测试添加问题"""
        result = self.vector_db.add_problem(
            problem_id="1",
            title="测试问题",
            description="这是一个测试问题的描述"
        )
        
        self.assertTrue(result, "添加问题应该成功")
    
    def test_add_problem_with_invalid_params(self):
        """测试使用无效参数添加问题"""
        with self.assertRaises(VectorDBException):
            self.vector_db.add_problem("", "测试问题", "描述")  # 空ID
        
        with self.assertRaises(VectorDBException):
            self.vector_db.add_problem("1", "", "描述")  # 空标题
    
    def test_update_problem(self):
        """测试更新问题"""
        # 先添加一个问题
        add_result = self.vector_db.add_problem(
            problem_id="1",
            title="原始标题",
            description="原始描述"
        )
        self.assertTrue(add_result, "添加问题应该成功")
        
        # 更新问题
        update_result = self.vector_db.update_problem(
            problem_id="1",
            title="更新后的标题",
            description="更新后的描述"
        )
        
        self.assertTrue(update_result, "更新问题应该成功")
    
    def test_search_similar_problems(self):
        """测试搜索相似问题"""
        # 添加一些测试数据
        self.vector_db.add_problem("1", "硬盘故障", "硬盘无法读取数据")
        self.vector_db.add_problem("2", "内存问题", "内存条不稳定")
        
        # 搜索相似问题
        results = self.vector_db.search_similar_problems("硬盘读取错误", n_results=5)
        
        self.assertIsInstance(results, list, "搜索结果应该是列表")
        self.assertGreaterEqual(len(results), 0, "应该返回至少0个结果")
    
    def test_search_similar_problems_with_empty_query(self):
        """测试使用空查询搜索相似问题"""
        with self.assertRaises(VectorDBException):
            self.vector_db.search_similar_problems("", n_results=5)
    
    def test_delete_problem(self):
        """测试删除问题"""
        # 先添加一个问题
        add_result = self.vector_db.add_problem(
            problem_id="1",
            title="测试问题",
            description="这是一个测试问题的描述"
        )
        self.assertTrue(add_result, "添加问题应该成功")
        
        # 删除问题
        delete_result = self.vector_db.delete_problem("1")
        self.assertTrue(delete_result, "删除问题应该成功")
    
    def test_batch_add_problems(self):
        """测试批量添加问题"""
        problems = [
            {
                'id': '1',
                'title': '问题1',
                'description': '描述1',
                'metadata': {'category': '硬件'}
            },
            {
                'id': '2',
                'title': '问题2',
                'description': '描述2',
                'metadata': {'category': '软件'}
            }
        ]
        
        result = self.vector_db.batch_add_problems(problems)
        
        self.assertEqual(result['success_count'], 2, "应该成功添加2个问题")
        self.assertEqual(len(result['failed_ids']), 0, "不应该有失败的ID")
    
    def test_get_problem(self):
        """测试获取问题"""
        # 添加一个测试问题
        self.vector_db.add_problem(
            problem_id="1",
            title="测试问题",
            description="这是一个测试问题的描述"
        )
        
        # 获取问题
        result = self.vector_db.get_problem("1")
        
        self.assertIsNotNone(result, "应该能够获取到问题")
        self.assertEqual(result['id'], "1", "问题ID应该匹配")
    
    def test_get_all_problems(self):
        """测试获取所有问题"""
        # 添加一些测试问题
        self.vector_db.add_problem("1", "问题1", "描述1")
        self.vector_db.add_problem("2", "问题2", "描述2")
        
        # 获取所有问题
        results = self.vector_db.get_all_problems()
        
        self.assertIsInstance(results, list, "结果应该是列表")
        self.assertGreaterEqual(len(results), 2, "应该至少有2个问题")


if __name__ == '__main__':
    unittest.main()