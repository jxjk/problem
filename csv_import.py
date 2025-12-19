"""
CSV导入功能模块
处理CSV文件的解析和数据导入到数据库
"""

import csv
import os
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from models import db, Problem, EquipmentType, ImportHistory, ProblemCategory, SolutionCategory
from ai_analysis import analyze_problem_with_ai, extract_category_from_ai_response


def _detect_csv_delimiter(sample_text: str) -> Optional[str]:
    """
    检测CSV文件的分隔符，包含错误处理和默认分隔符回退机制
    改进算法：更好地处理包含大量逗号的文本
    
    Args:
        sample_text: CSV文件内容样本
    
    Returns:
        str or None: 检测到的分隔符，如果检测失败返回None
    """
    if not sample_text:
        logger.warning("CSV样本文本为空，无法检测分隔符")
        return None

    # 首先尝试使用csv.Sniffer检测
    try:
        sniffer = csv.Sniffer()
        # 预处理文本，确保文本中包含足够的样本
        sample = sample_text[:2048]  # 增加样本大小到2048字符以更好处理复杂CSV
        delimiter = sniffer.sniff(sample, delimiters=',;\t|:').delimiter
        if delimiter:
            logger.info(f"使用csv.Sniffer检测到分隔符: {repr(delimiter)}")
            return delimiter
    except (csv.Error, TypeError, ValueError) as e:
        logger.warning(f"csv.Sniffer检测分隔符失败: {str(e)}")
        # 如果sniffer失败，继续尝试其他方法
        pass

    # 改进的分隔符检测算法：考虑分隔符在行中的分布和一致性
    delimiters = [',', ';', '\t', '|', ':', ' ']
    delimiter_scores = {}

    # 分割前几行来分析可能的分隔符
    lines = [line.strip() for line in sample_text.split('\n') if line.strip()]
    if len(lines) < 2:
        lines = [line.strip() for line in sample_text.split('\r') if line.strip()]
    if len(lines) < 2:
        lines = [line.strip() for line in sample_text.split('\r\n') if line.strip()]

    # 只分析前几行，防止样本过多，但 take at least 5 lines if available
    lines = lines[:min(20, len(lines))]  # 现在最多分析20行

    # 增强检测算法：计算分隔符的一致性，并考虑字段数量的分布
    for delimiter in delimiters:
        if not lines:
            continue

        # 计算每行中分隔符的数量和产生的字段数
        field_counts = []
        delimiter_counts = []
        total_delimiter_chars = 0  # 用于处理包含大量分隔符的情况

        for line in lines:
            if line.strip():
                delimiter_count = line.count(delimiter)
                field_count = delimiter_count + 1  # 分隔符数量+1等于字段数
                delimiter_counts.append(delimiter_count)
                field_counts.append(field_count)
                total_delimiter_chars += delimiter_count

        # 如果某个分隔符出现次数过多，可能不是真正的分隔符
        avg_delimiter_per_line = sum(delimiter_counts) / len(delimiter_counts) if delimiter_counts else 0
        if avg_delimiter_per_line > 20:  # 如果平均每行分隔符数量超过20，认为可能不是分隔符
            continue

        # 检查字段数量的一致性（这比简单的分隔符数量更准确）
        if field_counts and len(field_counts) >= 2:  # 至少需要2行来验证一致性
            # 更好的一致性评分算法
            avg_fields = sum(field_counts) / len(field_counts)
            variance = sum((x - avg_fields) ** 2 for x in field_counts) / len(field_counts) if len(field_counts) > 1 else 0
            std_dev = variance ** 0.5
            
            # 避免std_dev为0的情况（所有行字段数相同）
            if std_dev == 0 and len(set(field_counts)) == 1 and field_counts[0] > 1:
                # 所有行字段数相同且大于1，一致性最高
                consistency_score = 100
            elif std_dev == 0:
                # 如果标准差为0但字段数不一致，降低分数
                consistency_score = 1
            else:
                # 标准差越小，一致性越高，分数越高
                consistency_score = max(0.1, 10 / (std_dev + 0.1)) * 10  # 防止除以0

            # 同时考虑平均字段数量，字段数太少可能不是正确分隔符
            field_count_bonus = max(0, min(10, avg_fields))  # 字段数在1-10之间给分，超过10不额外加分

            # 综合评分：一致性 + 字段数奖励
            delimiter_scores[delimiter] = consistency_score * 0.7 + field_count_bonus * 0.3

    # 返回得分最高的分隔符
    if delimiter_scores:
        best_delimiter = max(delimiter_scores, key=delimiter_scores.get)
        best_score = delimiter_scores[best_delimiter]
        logger.info(f"分隔符检测结果: {repr(best_delimiter)} (得分: {best_score:.2f})")
        return best_delimiter
    else:
        # 如果所有方法都失败，返回默认的逗号分隔符
        logger.info("所有分隔符检测方法都失败，使用默认分隔符 ','")
        return ','

# 获取logger实例
logger = logging.getLogger(__name__)


def import_csv_file(file_path: str, fail_on_error: bool = False):
    """
    从CSV文件导入问题数据（改进版本，使用批量事务处理和更好的错误处理）
    添加枚举值验证、数据验证和清理功能
    实现不合格记录分离处理和统计功能，错误严重程度区分
    
    Args:
        file_path: CSV文件路径
        fail_on_error: 是否在遇到错误时立即失败，默认False继续处理有效记录
    
    Returns:
        dict: 包含导入结果的字典，包括成功和失败的记录统计
    """
    import time
    start_time = time.time()  # 记录开始时间用于性能监控
    
    # 导入配置
    from config import Config
    
    # 安全检查：验证文件路径，防止路径遍历攻击
    if '..' in file_path or file_path.startswith('/') or ':/' in file_path:
        logger.warning(f"非法文件路径检测: {file_path}")
        raise ValueError("非法文件路径")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"CSV文件不存在: {file_path}")
        raise FileNotFoundError(f"CSV文件不存在: {file_path}")
    
    # 检查文件大小
    file_size = os.path.getsize(file_path)
    max_size = getattr(Config, 'CSV_FILE_SIZE_LIMIT', 100 * 1024 * 1024)  # 默认100MB
    if file_size > max_size:
        logger.error(f"CSV文件大小超过限制: {file_size} > {max_size}")
        raise ValueError(f"CSV文件大小超过限制 ({max_size} bytes)")
    
    # 尝试不同的编码格式读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
    used_encoding = None
    sample = ''
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as test_file:
                # 读取前2048字节用于检测CSV格式
                sample = test_file.read(2048)
                used_encoding = encoding
                break
        except UnicodeDecodeError:
            continue
    
    if used_encoding is None:
        logger.error("无法识别文件编码")
        raise ValueError("无法识别文件编码，请确保文件为文本格式")
    
    # 检测CSV格式
    delimiter = _detect_csv_delimiter(sample)
    if delimiter is None:
        logger.error("无法检测CSV文件分隔符")
        raise ValueError("无法检测CSV文件分隔符，请确保文件为有效的CSV格式")
    
    # 验证CSV文件是否为空
    with open(file_path, 'r', encoding=used_encoding) as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        first_row = next(reader, None)
        if first_row is None:
            logger.info("CSV文件为空")
            return {'message': 'CSV文件为空', 'importedCount': 0, 'totalCount': 0, 'failedCount': 0, 'failedRecords': []}
    
    # 记录导入历史 - 在事务中创建
    import_history = ImportHistory(
        filename=os.path.basename(file_path),
        imported_by=1,  # 默认用户ID
        total_records=0,  # 临时值，稍后更新
        status='processing',
        started_at=datetime.now()
    )
    db.session.add(import_history)
    try:
        db.session.flush()  # 获取ID但不提交
        history_id = import_history.id
    except Exception as e:
        logger.error(f"创建导入历史记录失败: {str(e)}")
        db.session.rollback()
        raise

    # 重新用检测到的编码打开文件进行处理
    processed_count = 0
    total_count = 0
    failed_count = 0
    errors = []
    failed_records = []  # 存储失败的记录
    equipment_types_cache = {}  # 缓存设备类型，避免重复查询
    problem_categories_cache = {}  # 缓存问题分类，避免重复查询
    solution_categories_cache = {}  # 缓存解决方案分类，避免重复查询

    try:
        with open(file_path, 'r', encoding=used_encoding) as file:
            reader = csv.DictReader(file, delimiter=delimiter)
            
            # 批量处理数据，避免单个事务过大
            batch_size = getattr(Config, 'CSV_BATCH_SIZE', 100)
            batch_problems = []
            
            for row in reader:
                total_count += 1
                
                # 安全检查：限制处理的总行数，防止内存耗尽攻击
                if total_count > getattr(Config, 'CSV_MAX_ROWS', 10000):  # 限制最大行数，从配置中读取
                    logger.warning(f'CSV文件行数超过限制({getattr(Config, "CSV_MAX_ROWS", 10000)})，停止处理: {file_path}')
                    errors.append(f'CSV文件行数超过限制({getattr(Config, "CSV_MAX_ROWS", 10000)})，停止处理')
                    break

                try:
                    # 清理和验证数据
                    cleaned_data, row_errors = _clean_and_validate_data(row, total_count)
                    # 区分错误严重程度：致命错误和警告
                    fatal_errors = [error for error in row_errors if _is_fatal_error(error)]
                    warnings = [error for error in row_errors if not _is_fatal_error(error)]

                    # 如果有致命错误，根据fail_on_error参数决定是否继续
                    if fatal_errors:
                        failed_count += 1
                        failed_records.append({
                            'row': total_count,
                            'data': row,
                            'errors': fatal_errors,
                            'warnings': warnings
                        })
                        logger.error(f'第 {total_count} 行存在致命错误: {fatal_errors}')
                        
                        if fail_on_error:
                            raise ValueError(f"第 {total_count} 行存在致命错误: {fatal_errors}")
                        else:
                            continue  # 跳过此行，继续处理下一行

                    # 获取清理后的数据
                    title = cleaned_data['title']
                    description = cleaned_data['description']
                    equipment_type_name = cleaned_data['equipment_type_name']
                    phase = cleaned_data['phase']
                    discovered_by = cleaned_data['discovered_by']
                    discovered_at = cleaned_data['discovered_at']
                    priority = cleaned_data['priority']

                    # 如果标题和描述都为空则跳过
                    if not title and not description:
                        logger.debug(f"跳过第 {total_count} 行：标题和描述都为空")
                        continue
                    
                    # 根据设备类型名称获取ID，使用缓存
                    equipment_type_id = None
                    if equipment_type_name:
                        if equipment_type_name in equipment_types_cache:
                            equipment_type_id = equipment_types_cache[equipment_type_name]
                        else:
                            equipment_type = EquipmentType.query.filter_by(name=equipment_type_name).first()
                            if equipment_type:
                                equipment_type_id = equipment_type.id
                                equipment_types_cache[equipment_type_name] = equipment_type_id
                            else:
                                # 如果设备类型不存在，创建新的
                                equipment_type = EquipmentType(name=equipment_type_name)
                                db.session.add(equipment_type)
                                try:
                                    db.session.flush()  # 获取ID
                                    equipment_type_id = equipment_type.id
                                    equipment_types_cache[equipment_type_name] = equipment_type_id
                                except Exception as et_error:
                                    logger.error(f"创建设备类型失败: {str(et_error)}")
                                    fatal_error_msg = f"第 {total_count} 行: 创建设备类型失败 - {str(et_error)}"
                                    failed_count += 1
                                    failed_records.append({
                                        'row': total_count,
                                        'data': row,
                                        'errors': [fatal_error_msg],
                                        'warnings': warnings
                                    })
                                    if fail_on_error:
                                        raise ValueError(fatal_error_msg)
                                    continue  # 跳过此行，继续处理下一行

                    # 创建问题记录
                    problem = Problem(
                        title=title,
                        description=description,
                        equipment_type_id=equipment_type_id,
                        phase=phase,
                        discovered_by=discovered_by,
                        discovered_at=discovered_at,
                        priority=priority  # 添加优先级字段
                    )
                    
                    # 使用AI分析和分类
                    try:
                        ai_result = analyze_problem_with_ai(title, description, equipment_type=equipment_type_name, phase=phase)
                        problem.ai_analyzed = True
                        problem.ai_analysis = ai_result.get('analysis', '')
                        
                        # 从AI响应中提取分类信息
                        category_info = extract_category_from_ai_response(
                            ai_result.get('analysis', ''), 
                            title, 
                            description
                        )
                        
                        # 获取问题分类ID（使用缓存避免重复查询）
                        problem_category_id = category_info.get('problem_category_id')
                        if problem_category_id:
                            problem.problem_category_id = problem_category_id
                        else:
                            # 尝试从缓存中查找，如果不存在则创建默认分类
                            category_name = category_info.get('problem_category_name', '默认分类')
                            if category_name in problem_categories_cache:
                                problem.problem_category_id = problem_categories_cache[category_name]
                            else:
                                problem_category = ProblemCategory.query.filter_by(name=category_name).first()
                                if not problem_category:
                                    problem_category = ProblemCategory(name=category_name, description='系统默认分类')
                                    db.session.add(problem_category)
                                    db.session.flush()
                                problem.problem_category_id = problem_category.id
                                problem_categories_cache[category_name] = problem_category.id

                        # 获取解决方案分类ID（使用缓存避免重复查询）
                        solution_category_id = category_info.get('solution_category_id')
                        if solution_category_id:
                            problem.solution_category_id = solution_category_id
                        else:
                            # 尝试从缓存中查找，如果不存在则创建默认分类
                            category_name = category_info.get('solution_category_name', '默认解决方案')
                            if category_name in solution_categories_cache:
                                problem.solution_category_id = solution_categories_cache[category_name]
                            else:
                                solution_category = SolutionCategory.query.filter_by(name=category_name).first()
                                if not solution_category:
                                    solution_category = SolutionCategory(name=category_name, description='系统默认解决方案')
                                    db.session.add(solution_category)
                                    db.session.flush()
                                problem.solution_category_id = solution_category.id
                                solution_categories_cache[category_name] = solution_category.id

                        # 使用AI返回的优先级，但要验证它是否有效
                        ai_priority = category_info.get('priority', priority)  # 使用验证过的默认优先级
                        is_valid, error_msg = _validate_enum_value(ai_priority, ['low', 'medium', 'high', 'critical'], 'priority')
                        if is_valid:
                            problem.priority = ai_priority
                        else:
                            problem.priority = priority  # 使用验证过的默认优先级

                    except Exception as ai_error:
                        logger.error(f'AI分析失败: {str(ai_error)}', exc_info=True)
                        # AI分析失败时，仍然保存基础问题信息，但标记为未分析
                        problem.ai_analyzed = False
                        problem.ai_analysis = None
                        # 使用默认的分类ID（ID=1，通常是通用分类）或从数据库中获取一个有效ID
                        try:
                            # 确保问题分类有有效ID
                            if ProblemCategory.query.first() is None:
                                # 如果没有分类，创建一个默认分类
                                default_category = ProblemCategory(name='默认分类', description='系统默认问题分类')
                                db.session.add(default_category)
                                db.session.flush()
                                problem.problem_category_id = default_category.id
                            else:
                                # 使用第一个可用的问题分类
                                default_category = ProblemCategory.query.first()
                                problem.problem_category_id = default_category.id

                            # 确保解决方案分类有有效ID
                            if SolutionCategory.query.first() is None:
                                # 如果没有分类，创建一个默认分类
                                default_solution = SolutionCategory(name='默认解决方案', description='系统默认解决方案')
                                db.session.add(default_solution)
                                db.session.flush()
                                problem.solution_category_id = default_solution.id
                            else:
                                # 使用第一个可用的解决方案分类
                                default_solution = SolutionCategory.query.first()
                                problem.solution_category_id = default_solution.id
                        except Exception as cat_error:
                            logger.error(f'设置默认分类失败: {str(cat_error)}', exc_info=True)

                    # 添加到批量处理列表
                    batch_problems.append(problem)
                    
                    # 当批量达到指定大小时，提交事务
                    if len(batch_problems) >= batch_size:
                        _process_batch(batch_problems, logger)
                        processed_count += len(batch_problems)
                        batch_problems = []  # 清空批量列表
                        
                except Exception as row_error:
                    logger.error(f'处理CSV第 {total_count} 行时出错: {str(row_error)}', exc_info=True)
                    fatal_error_msg = f'第 {total_count} 行处理失败: {str(row_error)}'
                    failed_count += 1
                    failed_records.append({
                        'row': total_count,
                        'data': row,
                        'errors': [fatal_error_msg],
                        'warnings': []
                    })
                    if fail_on_error:
                        raise
                    continue  # 继续处理下一行

            # 处理最后一批数据
            if batch_problems:
                _process_batch(batch_problems, logger)
                processed_count += len(batch_problems)

    except Exception as e:
        logger.error(f'CSV文件处理过程中发生错误: {str(e)}', exc_info=True)
        # 回滚整个事务
        db.session.rollback()
        # 更新导入历史记录状态为失败
        try:
            import_history.status = 'failed'
            import_history.total_records = total_count
            import_history.processed_records = processed_count
            import_history.failed_records = failed_count
            import_history.error_log = '; '.join(errors[:20] + [str(e)]) if errors else str(e)  # 记录错误
            import_history.completed_at = datetime.now()
            db.session.commit()
        except Exception as rollback_error:
            logger.error(f'更新导入历史记录失败: {str(rollback_error)}')
        raise

    # 更新导入历史记录状态
    try:
        import_history.total_records = total_count
        import_history.status = 'completed'
        import_history.processed_records = processed_count
        import_history.failed_records = failed_count
        import_history.completed_at = datetime.now()
        if errors:
            import_history.error_log = '; '.join(errors[:20]) + ('...' if len(errors) > 20 else '')  # 只记录前20个错误，避免日志过长
        db.session.commit()
        logger.info(f'CSV导入完成: 总共 {total_count} 行，成功处理 {processed_count} 行，失败 {failed_count} 行')
    except Exception as final_error:
        logger.error(f'更新导入历史记录失败: {str(final_error)}')
        db.session.rollback()
        raise

    # 计算总处理时间
    total_processing_time = time.time() - start_time
    logger.info(f'CSV导入完成，总处理时间: {total_processing_time:.2f} 秒, '
                f'处理记录: {processed_count}/{total_count}，失败: {failed_count}')
    
    return {
        'message': f'CSV文件导入完成，成功处理 {processed_count} 条，失败 {failed_count} 条',
        'importedCount': processed_count,
        'failedCount': failed_count,
        'totalCount': total_count,
        'historyId': history_id,
        'processingTime': round(total_processing_time, 2),  # 添加处理时间信息
        'errorCount': len(errors),  # 添加错误计数
        'failedRecords': failed_records  # 返回失败记录详情
    }


def _process_batch(batch_problems, logger):
    """
    处理问题批量插入，包括向量数据库同步
    
    Args:
        batch_problems: 问题列表
        logger: 日志记录器
    """
    try:
        # 批量添加问题到数据库
        for problem in batch_problems:
            db.session.add(problem)
        db.session.flush()  # 获取问题ID但不提交事务

        # 提交数据库事务
        db.session.commit()

        # 将问题添加到向量数据库（异步处理或批量处理以提高性能）
        for problem in batch_problems:
            try:
                success = problem.save_to_vector_db()
                if not success:
                    logger.warning(f"无法将问题 {problem.id} 保存到向量数据库")
            except Exception as vector_error:
                logger.error(f"保存问题 {problem.id} 到向量数据库失败: {str(vector_error)}")

    except Exception as batch_error:
        logger.error(f'批量处理问题时出错: {str(batch_error)}', exc_info=True)
        db.session.rollback()
        raise


def _validate_enum_value(value: str, valid_values: List[str], field_name: str) -> Tuple[bool, str]:
    """
    验证枚举值是否有效

    Args:
        value: 要验证的值
        valid_values: 有效值列表
        field_name: 字段名称，用于错误信息

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息或空字符串)
    """
    if not value:
        return True, ""  # 空值被认为是有效的，由模型层处理默认值

    if value.lower() in [v.lower() for v in valid_values]:
        return True, ""
    else:
        return False, f"字段 '{field_name}' 包含无效的枚举值 '{value}'，有效值: {valid_values}"


def _clean_and_validate_data(row_data: Dict[str, Any], row_num: int) -> Tuple[Dict[str, Any], List[str]]:
    """
    清理和验证CSV行数据，增强错误处理和边界情况处理

    Args:
        row_data: CSV行数据字典
        row_num: 行号，用于错误报告

    Returns:
        Tuple[Dict[str, Any], List[str]]: (清理后的数据, 错误列表)
    """
    # 导入配置类
    from config import Config

    errors = []

    # 清理和验证标题
    title = _sanitize_input(str(row_data.get('title') or row_data.get('problem') or row_data.get('issue') or row_data.get('标题') or row_data.get('问题') or ''))
    title = title[:getattr(Config, 'CSV_TITLE_MAX_LENGTH', 500)] if title else ''

    # 清理和验证描述
    description = _sanitize_input(str(row_data.get('description') or row_data.get('reason') or row_data.get('analysis') or row_data.get('描述') or row_data.get('原因') or row_data.get('分析') or ''))
    description = description[:getattr(Config, 'CSV_DESCRIPTION_MAX_LENGTH', 2000)] if description else ''

    # 清理和验证设备类型
    equipment_type_name = _sanitize_input(str(row_data.get('equipment_type') or row_data.get('device_type') or row_data.get('设备类型') or ''))
    equipment_type_name = equipment_type_name[:getattr(Config, 'CSV_EQUIPMENT_TYPE_MAX_LENGTH', 100)] if equipment_type_name else ''

    # 验证并清理阶段字段（枚举值验证）
    phase = _sanitize_input(str(row_data.get('phase') or row_data.get('stage') or row_data.get('阶段') or 'design'))
    is_valid, error_msg = _validate_enum_value(phase, ['design', 'development', 'usage', 'maintenance'], 'phase')
    if not is_valid:
        errors.append(f"第 {row_num} 行: {error_msg}")
        phase = 'design'  # 使用默认值

    # 清理发现者字段
    discovered_by = _sanitize_input(str(row_data.get('discovered_by') or row_data.get('发现者') or ''))

    # 解析并验证发现时间
    discovered_at_str = row_data.get('discovered_at') or row_data.get('发现时间')
    discovered_at = None
    if discovered_at_str:
        try:
            # 尝试多种日期格式
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d %H:%M:%S', '%Y.%m.%d']
            for fmt in date_formats:
                try:
                    discovered_at = datetime.strptime(str(discovered_at_str), fmt).date()
                    break
                except ValueError:
                    continue
            if discovered_at is None:
                logger.warning(f"第 {row_num} 行: 日期格式无效 '{discovered_at_str}'，使用默认值")
        except Exception as date_error:
            logger.warning(f"第 {row_num} 行日期解析失败: {discovered_at_str}, 错误: {str(date_error)}")
            errors.append(f"第 {row_num} 行: 日期解析失败 '{discovered_at_str}'")
            discovered_at = None

    # 清理优先级字段（枚举值验证）
    priority = _sanitize_input(str(row_data.get('priority') or row_data.get('优先级') or 'medium'))
    is_valid, error_msg = _validate_enum_value(priority, ['low', 'medium', 'high', 'critical'], 'priority')
    if not is_valid:
        errors.append(f"第 {row_num} 行: {error_msg}")
        priority = 'medium'  # 使用默认值

    # 边界情况处理：检查是否存在过多的特殊字符，可能表示数据被污染
    special_char_threshold = getattr(Config, 'CSV_SPECIAL_CHAR_THRESHOLD', 0.5)  # 默认50%的字符为特殊字符时警告
    text_fields = [title, description, equipment_type_name, discovered_by]
    special_chars_count = 0
    total_chars = 0
    for field in text_fields:
        if field:
            import re
            # 计算特殊字符数量（除字母、数字、中文外的字符）
            special_chars = re.sub(r'[\w\u4e00-\u9fff]', '', field)
            special_chars_count += len(special_chars)
            total_chars += len(field)

    if total_chars > 0 and special_chars_count / total_chars > special_char_threshold:
        errors.append(f"第 {row_num} 行: 文本中特殊字符比例过高，可能存在数据污染")

    # 返回清理后的数据
    cleaned_data = {
        'title': title.strip(),
        'description': description.strip(),
        'equipment_type_name': equipment_type_name.strip(),
        'phase': phase,
        'discovered_by': discovered_by.strip(),
        'discovered_at': discovered_at,
        'priority': priority
    }

    return cleaned_data, errors


def _is_fatal_error(error_msg: str) -> bool:
    """
    判断错误是否为致命错误，需要阻止记录导入
    例如：数据库约束违反、严重数据格式错误等
    
    Args:
        error_msg: 错误消息字符串
    
    Returns:
        bool: 如果是致命错误返回True，否则返回False
    """
    fatal_keywords = [
        '数据库约束违反',
        '唯一性约束违反',
        '外键约束',
        '无法连接数据库',
        '内存溢出',
        '文件大小超限',
        '非法字符',
        'SQL注入尝试',
        '路径遍历攻击'
    ]
    return any(keyword in error_msg for keyword in fatal_keywords)


def _sanitize_input(input_str: str) -> str:
    """
    清理输入字符串，移除潜在的危险字符

    Args:
        input_str: 输入字符串

    Returns:
        str: 清理后的字符串
    """
    if input_str is None:
        return ''  # 统一返回空字符串而不是None，避免后续处理问题

    if not input_str:
        return ''

    # 确保输入是字符串
    input_str = str(input_str)

    # 移除潜在的危险字符和脚本标签
    import re
    # 移除潜在的恶意内容
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_str, flags=re.IGNORECASE|re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)  # 移除事件处理器
    sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE|re.DOTALL)  # 移除iframe
    sanitized = re.sub(r'<object[^>]*>.*?</object>', '', sanitized, flags=re.IGNORECASE|re.DOTALL)  # 移除object
    sanitized = re.sub(r'<embed[^>]*>.*?</embed>', '', sanitized, flags=re.IGNORECASE|re.DOTALL)  # 移除embed
    sanitized = re.sub(r'eval\s*\(', '', sanitized, flags=re.IGNORECASE)  # 移除eval函数调用
    sanitized = re.sub(r'document\.cookie', '', sanitized, flags=re.IGNORECASE)  # 移除document.cookie访问

    # 返回清理后的字符串，防止其他类型的注入
    return sanitized.strip()


def save_failed_records_to_csv(failed_records: List[Dict], output_file_path: str = None) -> str:
    """
    将不合格的记录保存到CSV文件中，便于用户查看和修正

    Args:
        failed_records: 失败记录列表
        output_file_path: 输出文件路径，如果为None则自动生成

    Returns:
        str: 保存的文件路径
    """
    import os
    from datetime import datetime

    if not failed_records:
        logger.info("没有失败记录需要保存")
        return ""

    # 如果没有指定输出路径，则生成默认路径
    if not output_file_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file_path = os.path.join('uploads', 'failed_records', f'failed_records_{timestamp}.csv')
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # 获取失败记录中的所有可能的字段名
    all_fieldnames = set()
    for record in failed_records:
        all_fieldnames.update(record['data'].keys())
    fieldnames = sorted(list(all_fieldnames))

    # 添加错误信息列
    fieldnames.extend(['error_info', 'row_number'])

    with open(output_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in failed_records:
            row_data = record['data'].copy()
            row_data['error_info'] = '; '.join(record['errors']) + ('; ' + '; '.join(record['warnings']) if record['warnings'] else '')
            row_data['row_number'] = record['row']
            writer.writerow(row_data)

    logger.info(f"失败记录已保存到: {output_file_path}")
    return output_file_path


def validate_csv_headers(file_path: str) -> Dict[str, Any]:
    """
    验证CSV文件的列头是否符合要求，包括枚举值验证

    Args:
        file_path: CSV文件路径

    Returns:
        dict: 包含验证结果的字典
    """
    required_headers = [
        ['title', 'problem', 'issue', '标题', '问题', 'title*', 'problem*', 'issue*'],  # 至少包含其中之一
        ['description', 'reason', 'analysis', '描述', '原因', '分析', 'description*', 'reason*', 'analysis*']  # 至少包含其中之一
    ]
    
    # 尝试不同的编码格式读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
    file_content = None
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                file_content = file.read()
                break
        except UnicodeDecodeError:
            continue
    
    if file_content is None:
        logger.error("无法识别CSV文件编码")
        return {
            'valid': False,
            'message': '无法识别文件编码，请确保文件为文本格式',
            'headers': []
        }
    
    # 使用StringIO和检测到的编码来处理CSV
    import io
    file_io = io.StringIO(file_content)
    
    # 检测CSV格式
    sample = file_content[:2048]  # 增加样本大小以更好地检测分隔符
    delimiter = _detect_csv_delimiter(sample)
    if delimiter is None:
        logger.error("验证CSV头部时无法检测分隔符")
        return {
            'valid': False,
            'message': '无法检测CSV文件分隔符，请确保文件为有效的CSV格式',
            'headers': []
        }
    
    reader = csv.DictReader(file_io, delimiter=delimiter)
    headers = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []  # 转换为小写进行比较

    # 检查是否包含必需的列
    missing_required = []
    for group in required_headers:
        found = any(h in headers for h in group)
        if not found:
            missing_required.append(' 或 '.join(group))
    
    if missing_required:
        logger.info(f"CSV文件缺少必需的列: {', '.join(missing_required)}")
        return {
            'valid': False,
            'message': f'缺少必需的列: {", ".join(missing_required)}',
            'headers': headers
        }

    # 额外验证：检查可选列是否使用了正确的枚举值
    validation_warnings = []
    for row in csv.DictReader(io.StringIO(file_content), delimiter=delimiter):
        # 验证阶段字段
        phase_value = row.get('phase') or row.get('stage') or row.get('阶段')
        if phase_value:
            is_valid, error_msg = _validate_enum_value(str(phase_value), ['design', 'development', 'usage', 'maintenance'], 'phase')
            if not is_valid:
                validation_warnings.append(error_msg)

        # 验证优先级字段
        priority_value = row.get('priority') or row.get('优先级')
        if priority_value:
            is_valid, error_msg = _validate_enum_value(str(priority_value), ['low', 'medium', 'high', 'critical'], 'priority')
            if not is_valid:
                validation_warnings.append(error_msg)

        break  # 只检查第一行以验证枚举值格式

    if validation_warnings:
        logger.warning(f"CSV文件包含验证警告: {'; '.join(validation_warnings[:5])}")
        return {
            'valid': True,  # 仍然认为有效，但有警告
            'message': f'CSV文件格式验证通过，但包含警告: {"; ".join(validation_warnings[:5])}',
            'headers': headers,
            'warnings': validation_warnings
        }
    
    logger.info(f"CSV文件格式验证通过，找到列: {headers}")
    return {
        'valid': True,
        'message': 'CSV文件格式验证通过',
        'headers': headers
    }
