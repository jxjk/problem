"""
向量数据库模块
使用ChromaDB作为向量数据库存储和检索问题相似性
"""
import logging
from typing import List, Dict, Optional, Tuple
from config import Config

# 尝试导入依赖，如果失败则提供降级功能
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import numpy as np
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB or SentenceTransformer not available. VectorDB will be disabled.")


class VectorDBException(Exception):
    """向量数据库自定义异常"""
    pass


class VectorDB:
    """
    向量数据库管理类，用于存储和检索问题的向量表示
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout  # 添加超时设置
        self.client = None
        self.model = None
        self.problems_collection = None

        if CHROMA_AVAILABLE:
            try:
                # 初始化ChromaDB客户端
                self.client = chromadb.Client(Settings(
                    persist_directory=Config.VECTOR_DB_PERSIST_DIR,  # 使用配置文件中的持久化存储路径
                    is_persistent=True,
                    anonymized_telemetry=False,  # 禁用遥测以保护隐私
                    allow_reset=True  # 允许重置
                ))
                
                # 初始化嵌入模型
                self.model = SentenceTransformer(Config.EMBEDDING_MODEL_NAME, device='cpu')  # 使用CPU避免GPU内存问题
                
                # 获取或创建问题集合
                self.problems_collection = self.client.get_or_create_collection(
                    name="problems",
                    metadata={"hnsw:space": "cosine"}  # 使用余弦距离计算相似度
                )
            except Exception as e:
                logging.error(f"初始化ChromaDB失败: {e}")
                CHROMA_AVAILABLE = False
        else:
            logging.warning("VectorDB running in degraded mode. Some functionality may be limited.")
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
    def _validate_inputs(self, problem_id: str, title: str = None, description: str = None) -> None:
        """验证输入参数"""
        if not problem_id or not str(problem_id).strip():
            raise VectorDBException("问题ID不能为空")
        if title is not None and (not title or not title.strip()):
            raise VectorDBException("问题标题不能为空")
        if description is not None and description and len(description.strip()) > 10000:  # 限制描述长度
            raise VectorDBException("问题描述长度不能超过10000字符")

    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量，包含错误处理和长度限制"""
        if not text or not text.strip():
            raise VectorDBException("文本内容不能为空")
        # 限制文本长度避免内存溢出
        text = text[:5000] if len(text) > 5000 else text
        try:
            embedding = self.model.encode([text], normalize_embeddings=True)[0].tolist()
            return embedding
        except Exception as e:
            self.logger.error(f"生成嵌入向量失败: {str(e)}")
            raise VectorDBException(f"生成嵌入向量失败: {str(e)}")
        
    def add_problem(self, problem_id: str, title: str, description: str, metadata: Dict = None) -> bool:
        """
        添加问题到向量数据库
        
        Args:
            problem_id: 问题ID
            title: 问题标题
            description: 问题描述
            metadata: 问题元数据
        
        Returns:
            bool: 添加是否成功
        """
        try:
            # 验证参数
            self._validate_inputs(problem_id, title, description)
            
            if not CHROMA_AVAILABLE:
                # 降级模式：记录警告但返回成功
                self.logger.warning(f"VectorDB not available. Would add problem {problem_id} in normal mode.")
                return True
            
            # 组合标题和描述作为文本内容
            content = f"{title} {description}".strip()
            if not content:
                raise VectorDBException("问题内容不能为空")
            
            # 生成嵌入向量
            embedding = self._generate_embedding(content)
            
            # 准备元数据
            if metadata is None:
                metadata = {}
            metadata['problem_id'] = str(problem_id)
            metadata['title'] = title
            metadata['description'] = description or ""
            metadata['created_at'] = str(metadata.get('created_at', ''))  # 保持原有创建时间
            
            # 检查问题是否已存在，如果存在则更新
            existing_problem = self.get_problem(problem_id)
            if existing_problem:
                self.logger.warning(f"问题 {problem_id} 已存在于向量数据库中，将进行更新操作")
                return self.update_problem(problem_id, title, description, metadata)
            
            # 添加到向量数据库
            self.problems_collection.add(
                embeddings=[embedding],
                ids=[str(problem_id)],
                metadatas=[metadata]
            )
            
            self.logger.info(f"问题 {problem_id} 已添加到向量数据库")
            return True
            
        except VectorDBException:
            raise
        except Exception as e:
            self.logger.error(f"添加问题到向量数据库失败: {str(e)}")
            raise VectorDBException(f"添加问题到向量数据库失败: {str(e)}")
    
    def batch_add_problems(self, problems: List[Dict]) -> Dict[str, Any]:
        """
        批量添加问题到向量数据库（优化版本，返回更详细的统计信息）
        
        Args:
            problems: 问题列表，每个元素包含'id', 'title', 'description', 'metadata'
        
        Returns:
            Dict[str, Any]: 包含成功数量、失败ID列表和详细统计的字典
        """
        try:
            if not problems:
                return {
                    'success_count': 0,
                    'failed_ids': [],
                    'total_processed': 0,
                    'errors': []
                }
            
            if not CHROMA_AVAILABLE:
                # 降级模式：记录警告但返回成功
                self.logger.warning(f"VectorDB not available. Would batch add {len(problems)} problems in normal mode.")
                return {
                    'success_count': len(problems),
                    'failed_ids': [],
                    'total_processed': len(problems),
                    'errors': []
                }
            
            # 准备批量数据
            ids = []
            embeddings = []
            metadatas = []
            failed_items = []
            errors = []
            processed_count = 0
            
            for problem in problems:
                try:
                    problem_id = str(problem.get('id', ''))
                    title = problem.get('title', '')
                    description = problem.get('description', '')
                    metadata = problem.get('metadata', {})
                    
                    # 验证必要参数
                    if not problem_id or not title or not title.strip():
                        failed_items.append(problem_id)
                        errors.append(f"问题 {problem_id} 缺少必要参数: id={problem_id}, title={title}")
                        continue
                    
                    # 组合标题和描述
                    content = f"{title} {description}".strip()
                    if not content:
                        failed_items.append(problem_id)
                        errors.append(f"问题 {problem_id} 内容为空")
                        continue
                    
                    # 生成嵌入向量
                    embedding = self._generate_embedding(content)
                    
                    # 准备元数据
                    metadata['problem_id'] = problem_id
                    metadata['title'] = title
                    metadata['description'] = description or ""
                    metadata['created_at'] = str(metadata.get('created_at', ''))
                    
                    # 添加到批量列表
                    ids.append(problem_id)
                    embeddings.append(embedding)
                    metadatas.append(metadata)
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"处理问题 {problem.get('id')} 时出错: {str(e)}")
                    failed_items.append(problem.get('id'))
                    errors.append(f"问题 {problem.get('id')} 处理失败: {str(e)}")
            
            # 执行批量添加 - 按批次处理以避免内存问题
            batch_size = 100  # 限制批次大小
            total_success = 0
            
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                
                try:
                    self.problems_collection.add(
                        embeddings=batch_embeddings,
                        ids=batch_ids,
                        metadatas=batch_metadatas
                    )
                    total_success += len(batch_ids)
                except Exception as e:
                    self.logger.error(f"批量添加批次失败: {str(e)}")
                    # 尝试逐个添加失败的项目
                    for idx, (bid, bemb, bmeta) in enumerate(zip(batch_ids, batch_embeddings, batch_metadatas)):
                        try:
                            self.problems_collection.add(
                                embeddings=[bemb],
                                ids=[bid],
                                metadatas=[bmeta]
                            )
                            total_success += 1
                        except Exception as item_error:
                            self.logger.error(f"添加单个项目 {bid} 失败: {str(item_error)}")
                            failed_items.append(bid)
                            errors.append(f"问题 {bid} 单个添加失败: {str(item_error)}")
            
            result = {
                'success_count': total_success,
                'failed_ids': failed_items,
                'total_processed': processed_count,
                'errors': errors
            }
            
            self.logger.info(f"批量添加问题完成: 成功 {total_success} 个, 失败 {len(failed_items)} 个, 总处理 {processed_count} 个")
            return result
            
        except Exception as e:
            self.logger.error(f"批量添加问题失败: {str(e)}")
            raise VectorDBException(f"批量添加问题失败: {str(e)}")
    
    def search_similar_problems(self, query: str, n_results: int = None, min_similarity: float = 0.0) -> List[Dict]:
        """
        搜索相似问题，增加最小相似度阈值
        
        Args:
            query: 查询文本
            n_results: 返回结果数量，默认使用配置值
            min_similarity: 最小相似度阈值（0-1之间）
        
        Returns:
            List[Dict]: 相似问题列表
        """
        try:
            if n_results is None:
                n_results = Config.VECTOR_DB_SEARCH_LIMIT
            
            # 验证查询文本
            if not query or not query.strip():
                raise VectorDBException("查询文本不能为空")
            
            if not CHROMA_AVAILABLE:
                # 降级模式：返回空结果
                self.logger.warning("VectorDB not available. Returning empty results for similarity search.")
                return []
            
            # 生成查询嵌入向量
            query_embedding = self._generate_embedding(query.strip())
            
            # 搜索相似问题
            from chromadb.api.types import QueryResult
            results: QueryResult = self.problems_collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results * 2, 100)  # 搜索更多结果以过滤低相似度
            )
            
            # 格式化结果并过滤低相似度
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results['distances'] else None
                    similarity_score = 1 - distance if distance is not None else 0
                    
                    # 过滤低相似度结果
                    if similarity_score >= min_similarity:
                        problem_result = {
                            'id': results['ids'][0][i],
                            'distance': distance,
                            'similarity_score': similarity_score,
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else None
                        }
                        formatted_results.append(problem_result)
            
            # 按相似度排序并限制结果数量
            formatted_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            formatted_results = formatted_results[:n_results]
            
            self.logger.info(f"搜索相似问题完成，找到 {len(formatted_results)} 个满足条件的结果")
            return formatted_results
            
        except VectorDBException:
            raise
        except Exception as e:
            self.logger.error(f"搜索相似问题失败: {str(e)}")
            raise VectorDBException(f"搜索相似问题失败: {str(e)}")
    
    def update_problem(self, problem_id: str, title: str, description: str, metadata: Dict = None) -> bool:
        """
        更新向量数据库中的问题
        
        Args:
            problem_id: 问题ID
            title: 问题标题
            description: 问题描述
            metadata: 问题元数据
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 验证参数
            self._validate_inputs(problem_id, title, description)
            
            if not CHROMA_AVAILABLE:
                # 降级模式：记录警告但返回成功
                self.logger.warning(f"VectorDB not available. Would update problem {problem_id} in normal mode.")
                return True
            
            # 检查问题是否存在
            existing_problem = self.get_problem(problem_id)
            if not existing_problem:
                raise VectorDBException(f"问题 {problem_id} 在向量数据库中不存在，无法更新")
            
            # 组合标题和描述作为文本内容
            content = f"{title} {description}".strip()
            if not content:
                raise VectorDBException("问题内容不能为空")
            
            # 生成嵌入向量
            embedding = self._generate_embedding(content)
            
            # 准备元数据
            if metadata is None:
                metadata = existing_problem.get('metadata', {})
            else:
                # 合并现有元数据和新元数据
                existing_meta = existing_problem.get('metadata', {})
                metadata = {**existing_meta, **metadata}
            metadata['problem_id'] = str(problem_id)
            metadata['title'] = title
            metadata['description'] = description or ""
            metadata['updated_at'] = str(metadata.get('updated_at', ''))  # 保持更新时间
            
            # 使用ChromaDB的update方法
            self.problems_collection.update(
                embeddings=[embedding],
                ids=[str(problem_id)],
                metadatas=[metadata]
            )
            
            self.logger.info(f"问题 {problem_id} 已在向量数据库中更新")
            return True
            
        except VectorDBException:
            raise
        except Exception as e:
            self.logger.error(f"更新问题在向量数据库中失败: {str(e)}")
            raise VectorDBException(f"更新问题在向量数据库中失败: {str(e)}")
    
    def delete_problem(self, problem_id: str) -> bool:
        """
        从向量数据库中删除问题
        
        Args:
            problem_id: 问题ID
        
        Returns:
            bool: 删除是否成功
        """
        try:
            if not problem_id or not str(problem_id).strip():
                raise VectorDBException("问题ID不能为空")
            
            if not CHROMA_AVAILABLE:
                # 降级模式：记录警告但返回成功
                self.logger.warning(f"VectorDB not available. Would delete problem {problem_id} in normal mode.")
                return True
            
            # 检查问题是否存在
            existing_problem = self.get_problem(problem_id)
            if not existing_problem:
                self.logger.warning(f"问题 {problem_id} 在向量数据库中不存在，跳过删除操作")
                return True  # 返回True表示操作成功（尽管问题不存在）
            
            self.problems_collection.delete(ids=[str(problem_id)])
            self.logger.info(f"问题 {problem_id} 已从向量数据库中删除")
            return True
            
        except VectorDBException:
            raise
        except Exception as e:
            self.logger.error(f"从向量数据库删除问题失败: {str(e)}")
            raise VectorDBException(f"从向量数据库删除问题失败: {str(e)}")
    
    def get_problem(self, problem_id: str) -> Optional[Dict]:
        """
        根据ID获取问题详情
        
        Args:
            problem_id: 问题ID
        
        Returns:
            Optional[Dict]: 问题详情
        """
        try:
            if not problem_id or not str(problem_id).strip():
                raise VectorDBException("问题ID不能为空")
            
            if not CHROMA_AVAILABLE:
                # 降级模式：返回None表示未找到
                self.logger.warning("VectorDB not available. Returning None for get_problem.")
                return None
                
            result = self.problems_collection.get(
                ids=[str(problem_id)]
            )
            
            if result['ids'] and len(result['ids']) > 0:
                return {
                    'id': result['ids'][0],
                    'embedding': result['embeddings'][0] if result['embeddings'] else None,
                    'metadata': result['metadatas'][0] if result['metadatas'] else None
                }
            
            self.logger.info(f"问题 {problem_id} 在向量数据库中不存在")
            return None
            
        except VectorDBException:
            raise
        except Exception as e:
            self.logger.error(f"获取问题详情失败: {str(e)}")
            raise VectorDBException(f"获取问题详情失败: {str(e)}")
    
    def get_all_problems(self, limit: int = None) -> List[Dict]:
        """
        获取所有问题，支持限制数量
        
        Args:
            limit: 限制返回结果数量，None表示不限制
        
        Returns:
            List[Dict]: 所有问题列表
        """
        try:
            if not CHROMA_AVAILABLE:
                # 降级模式：返回空列表
                self.logger.warning("VectorDB not available. Returning empty list for get_all_problems.")
                return []
            
            # 使用where条件获取所有数据，或限制数量
            results = self.problems_collection.get(limit=limit)
            
            problems = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    problem = {
                        'id': results['ids'][i],
                        'embedding': results['embeddings'][i] if results['embeddings'] else None,
                        'metadata': results['metadatas'][i] if results['metadatas'] else None
                    }
                    problems.append(problem)
            
            self.logger.info(f"成功获取 {len(problems)} 个问题")
            return problems
            
        except Exception as e:
            self.logger.error(f"获取所有问题失败: {str(e)}")
            raise VectorDBException(f"获取所有问题失败: {str(e)}")
    
    def get_problem_count(self) -> int:
        """
        获取向量数据库中问题总数
        
        Returns:
            int: 问题总数
        """
        try:
            if not CHROMA_AVAILABLE:
                return 0
            return self.problems_collection.count()
        except Exception as e:
            self.logger.error(f"获取问题总数失败: {str(e)}")
            return 0
    
    def clear_collection(self) -> bool:
        """
        清空整个向量数据库集合（谨慎使用）
        
        Returns:
            bool: 清空是否成功
        """
        try:
            if not CHROMA_AVAILABLE:
                self.logger.warning("VectorDB not available. Would clear collection in normal mode.")
                return True
            
            # 获取所有问题ID，然后批量删除
            all_problems = self.get_all_problems()
            if all_problems:
                ids = [problem['id'] for problem in all_problems]
                self.problems_collection.delete(ids=ids)
                self.logger.info(f"已清空向量数据库，删除了 {len(ids)} 个问题")
            else:
                self.logger.info("向量数据库已为空，无需清空")
            return True
        except Exception as e:
            self.logger.error(f"清空向量数据库失败: {str(e)}")
            raise VectorDBException(f"清空向量数据库失败: {str(e)}")


# 全局向量数据库实例
vector_db = None


def init_vector_db():
    """
    初始化向量数据库
    """
    global vector_db
    if vector_db is None:
        vector_db = VectorDB()
    return vector_db


def get_vector_db():
    """
    获取向量数据库实例
    """
    global vector_db
    if vector_db is None:
        vector_db = VectorDB()
    return vector_db