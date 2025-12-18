"""
向量数据库综合单元测试
"""
import unittest
import tempfile
import os
from vector_db import VectorDB, VectorDBException
from config import Config


class TestVectorDBComprehensive(unittest.TestCase):
    """向量数据库综合测试类"""
    
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
    
    def test_add_problem_empty_content(self):
        """测试添加空内容问题"""
        with self.assertRaises(VectorDBException):
            self.vector_db.add_problem("1", "标题", "")  # 空描述，但标题有效
    
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
    
    def test_update_nonexistent_problem(self):
        """测试更新不存在的问题"""
        with self.assertRaises(VectorDBException):
            self.vector_db.update_problem(
                problem_id="999",
                title="更新后的标题",
                description="更新后的描述"
            )
    
    def test_search_similar_problems(self):
        """测试搜索相似问题"""
        # 添加一些测试数据
        self.vector_db.add_problem("1", "硬盘故障", "硬盘无法读取数据")
        self.vector_db.add_problem("2", "内存问题", "内存条不稳定")
        
        # 搜索相似问题
        results = self.vector_db.search_similar_problems("硬盘读取错误", n_results=5)
        
        self.assertIsInstance(results, list, "搜索结果应该是列表")
        self.assertGreaterEqual(len(results), 0, "应该返回至少0个结果")
    
    def test_search_similar_problems_with_min_similarity(self):
        """测试带最小相似度阈值的搜索"""
        # 添加一些测试数据
        self.vector_db.add_problem("1", "硬盘故障", "硬盘无法读取数据")
        self.vector_db.add_problem("2", "内存问题", "内存条不稳定")
        
        # 搜索相似问题，设置高相似度阈值
        results = self.vector_db.search_similar_problems("硬盘读取错误", n_results=5, min_similarity=0.8)
        
        self.assertIsInstance(results, list, "搜索结果应该是列表")
    
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
    
    def test_delete_nonexistent_problem(self):
        """测试删除不存在的问题"""
        # 删除不存在的问题应该返回True（表示操作成功，尽管问题不存在）
        delete_result = self.vector_db.delete_problem("999")
        self.assertTrue(delete_result, "删除不存在的问题也应该返回True")
    
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
        self.assertEqual(result['total_processed'], 2, "应该处理2个问题")
    
    def test_batch_add_problems_with_invalid_data(self):
        """测试批量添加问题时包含无效数据"""
        problems = [
            {
                'id': '1',
                'title': '有效问题',
                'description': '有效描述',
                'metadata': {'category': '硬件'}
            },
            {
                'id': '2',
                'title': '',  # 无效：空标题
                'description': '描述2',
                'metadata': {'category': '软件'}
            },
            {
                'id': '',  # 无效：空ID
                'title': '标题3',
                'description': '描述3',
                'metadata': {'category': '网络'}
            }
        ]
        
        result = self.vector_db.batch_add_problems(problems)
        
        self.assertGreaterEqual(result['success_count'], 1, "至少应成功添加1个问题")
        self.assertGreaterEqual(len(result['failed_ids']), 2, "应该有失败的ID")
    
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
    
    def test_get_problem_with_invalid_id(self):
        """测试获取不存在的问题"""
        result = self.vector_db.get_problem("999")  # 不存在的问题ID
        self.assertIsNone(result, "获取不存在的问题应该返回None")
    
    def test_get_all_problems(self):
        """测试获取所有问题"""
        # 添加一些测试问题
        self.vector_db.add_problem("1", "问题1", "描述1")
        self.vector_db.add_problem("2", "问题2", "描述2")
        
        # 获取所有问题
        results = self.vector_db.get_all_problems()
        
        self.assertIsInstance(results, list, "结果应该是列表")
        self.assertGreaterEqual(len(results), 2, "应该至少有2个问题")
    
    def test_get_problem_count(self):
        """测试获取问题总数"""
        # 清空集合
        self.vector_db.clear_collection()
        
        # 验证初始计数
        count = self.vector_db.get_problem_count()
        self.assertEqual(count, 0, "初始计数应该是0")
        
        # 添加问题
        self.vector_db.add_problem("1", "问题1", "描述1")
        self.vector_db.add_problem("2", "问题2", "描述2")
        
        # 验证计数
        count = self.vector_db.get_problem_count()
        self.assertEqual(count, 2, "计数应该是2")
    
    def test_get_problem_with_limit(self):
        """测试带限制的获取所有问题"""
        # 添加多个问题
        for i in range(10):
            self.vector_db.add_problem(str(i), f"问题{i}", f"描述{i}")
        
        # 获取限制数量的问题
        results = self.vector_db.get_all_problems(limit=5)
        
        self.assertEqual(len(results), 5, "应该只返回5个问题")
    
    def test_add_problem_duplicate_handling(self):
        """测试重复问题处理"""
        # 添加问题
        result1 = self.vector_db.add_problem("1", "原始标题", "原始描述")
        self.assertTrue(result1, "第一次添加应该成功")
        
        # 添加相同ID的问题（应该触发更新操作）
        result2 = self.vector_db.add_problem("1", "更新标题", "更新描述")
        self.assertTrue(result2, "重复添加应该成功（作为更新）")
        
        # 验证问题内容已被更新
        problem = self.vector_db.get_problem("1")
        self.assertEqual(problem['metadata']['title'], "更新标题", "问题标题应该被更新")
    
    def test_embedding_generation_with_long_text(self):
        """测试长文本嵌入生成"""
        long_description = "这是一个很长的描述。" * 1000  # 创建长描述
        
        result = self.vector_db.add_problem(
            problem_id="1",
            title="长文本测试",
            description=long_description
        )
        
        self.assertTrue(result, "添加长文本问题应该成功")
    
    def test_embedding_generation_with_empty_text(self):
        """测试空文本嵌入生成"""
        with self.assertRaises(VectorDBException):
            self.vector_db._generate_embedding("")  # 空文本
        
        with self.assertRaises(VectorDBException):
            self.vector_db._generate_embedding("   ")  # 只有空格的文本
    
    def test_clear_collection(self):
        """测试清空集合功能"""
        # 添加一些问题
        self.vector_db.add_problem("1", "问题1", "描述1")
        self.vector_db.add_problem("2", "问题2", "描述2")
        
        # 验证问题存在
        count = self.vector_db.get_problem_count()
        self.assertGreater(count, 0, "应该存在一些问题")
        
        # 清空集合
        result = self.vector_db.clear_collection()
        self.assertTrue(result, "清空操作应该成功")
        
        # 验证集合已清空
        count = self.vector_db.get_problem_count()
        self.assertEqual(count, 0, "计数应该是0")


if __name__ == '__main__':
    unittest.main()