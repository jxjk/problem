"""
CSV导入功能模块
处理CSV文件的解析和数据导入到数据库
"""

import csv
import os
from datetime import datetime
from models import db, Problem, EquipmentType, ImportHistory
from ai_analysis import analyze_problem_with_ai, extract_category_from_ai_response


def import_csv_file(file_path):
    """
    从CSV文件导入问题数据（流式处理版本，增强安全验证）
    
    Args:
        file_path: CSV文件路径
    
    Returns:
        dict: 包含导入结果的字典
    """
    # 导入配置
    from config import Config
    
    # 安全检查：验证文件路径，防止路径遍历攻击
    if '..' in file_path or file_path.startswith('/') or ':/' in file_path:
        raise ValueError("非法文件路径")
    
    # 尝试不同的编码格式读取CSV文件
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
    file_handle = None
    used_encoding = None
    
    for encoding in encodings:
        try:
            file_handle = open(file_path, 'r', encoding=encoding)
            # 读取前1024字节用于检测CSV格式
            sample = file_handle.read(1024)
            file_handle.seek(0)  # 回到文件开头
            used_encoding = encoding
            break
        except UnicodeDecodeError:
            continue
    
    if file_handle is None:
        raise ValueError("无法识别文件编码，请确保文件为文本格式")
    
    # 检测CSV格式
    sniffer = csv.Sniffer()
    delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
    
    reader = csv.DictReader(file_handle, delimiter=delimiter)
    
    # 验证CSV文件是否为空
    first_row = next(reader, None)
    if first_row is None:
        file_handle.close()
        return {'message': 'CSV文件为空', 'importedCount': 0, 'totalCount': 0}
    
    # 记录导入历史
    import_history = ImportHistory(
        filename=os.path.basename(file_path),
        imported_by=1,  # 默认用户ID
        total_records=0,  # 临时值，稍后更新
        status='processing',
        started_at=datetime.now()
    )
    db.session.add(import_history)
    db.session.flush()  # 获取ID但不提交
    
    processed_count = 0
    total_count = 0
    
    # 重新打开文件进行处理（因为上面已经读取过一部分）
    file_handle.close()
    
    # 重新用检测到的编码打开文件
    with open(file_path, 'r', encoding=used_encoding) as file:
        reader = csv.DictReader(file, delimiter=delimiter)
        
        for row in reader:
            total_count += 1
            
            # 安全检查：限制处理的总行数，防止内存耗尽攻击
            if total_count > Config.CSV_MAX_ROWS:  # 限制最大行数，从配置中读取
                app.logger.warning(f'CSV文件行数超过限制({Config.CSV_MAX_ROWS})，停止处理: {file_path}')
                break
            
            try:
                # 提取CSV数据，支持中英文列名
                title = (
                    row.get('title') or 
                    row.get('problem') or 
                    row.get('issue') or 
                    row.get('标题') or 
                    row.get('问题') or 
                    ''
                )
                description = (
                    row.get('description') or 
                    row.get('reason') or 
                    row.get('analysis') or 
                    row.get('描述') or 
                    row.get('原因') or 
                    row.get('分析') or 
                    ''
                )
                equipment_type_name = (
                    row.get('equipment_type') or 
                    row.get('device_type') or 
                    row.get('设备类型') or 
                    ''
                )
                phase = (
                    row.get('phase') or 
                    row.get('stage') or 
                    row.get('阶段') or 
                    'design'
                )
                discovered_by = (
                    row.get('discovered_by') or 
                    row.get('发现者') or 
                    ''
                )
                discovered_at_str = (
                    row.get('discovered_at') or 
                    row.get('发现时间') or 
                    None
                )
                
                # 安全检查：清理和验证输入数据
                title = _sanitize_input(str(title)[:Config.CSV_TITLE_MAX_LENGTH]) if title else ''  # 限制长度
                description = _sanitize_input(str(description)[:Config.CSV_DESCRIPTION_MAX_LENGTH]) if description else ''  # 限制长度
                equipment_type_name = _sanitize_input(str(equipment_type_name)[:Config.CSV_EQUIPMENT_TYPE_MAX_LENGTH]) if equipment_type_name else ''
                
                # 如果标题和描述都为空则跳过
                if not title and not description:
                    continue
                
                # 解析发现时间
                discovered_at = None
                if discovered_at_str:
                    try:
                        # 尝试多种日期格式
                        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%d-%m-%Y'):
                            try:
                                discovered_at = datetime.strptime(discovered_at_str, fmt).date()
                                break
                            except ValueError:
                                continue
                    except:
                        discovered_at = None
                
                # 根据设备类型名称获取ID
                equipment_type_id = None
                if equipment_type_name:
                    equipment_type = EquipmentType.query.filter_by(name=equipment_type_name).first()
                    if equipment_type:
                        equipment_type_id = equipment_type.id
                    else:
                        # 如果设备类型不存在，创建新的
                        # 安全检查：确保设备类型名称已清理
                        equipment_type = EquipmentType(name=equipment_type_name)
                        db.session.add(equipment_type)
                        db.session.flush()  # 获取ID
                        equipment_type_id = equipment_type.id
                
                # 创建问题记录
                problem = Problem(
                    title=title,
                    description=description,
                    equipment_type_id=equipment_type_id,
                    phase=phase,
                    discovered_by=discovered_by,
                    discovered_at=discovered_at
                )
                
                db.session.add(problem)
                db.session.flush()  # 获取问题ID
                
                # 使用AI分析和分类
                try:
                    ai_result = analyze_problem_with_ai(title, description)
                    problem.ai_analyzed = True
                    problem.ai_analysis = ai_result.get('analysis', '')
                    
                    # 从AI响应中提取分类信息
                    category_info = extract_category_from_ai_response(
                        ai_result.get('analysis', ''), 
                        title, 
                        description
                    )
                    
                    problem.problem_category_id = category_info.get('problem_category_id', 1)
                    problem.solution_category_id = category_info.get('solution_category_id', 1)
                    problem.priority = category_info.get('priority', 'medium')
                    
                except Exception as e:
                    app.logger.error(f'AI分析失败: {str(e)}')
                    # AI分析失败时，仍然保存基础问题信息，但标记为未分析
                    problem.ai_analyzed = False
                    problem.ai_analysis = None
                
                # 提交当前问题记录
                db.session.commit()
                
                processed_count += 1
                
            except Exception as e:
                app.logger.error(f'处理CSV行时出错: {str(e)}')
                continue  # 继续处理下一行
    
    # 更新导入历史记录状态
    import_history.total_records = total_count
    import_history.status = 'completed'
    import_history.processed_records = processed_count
    import_history.completed_at = datetime.now()
    
    db.session.commit()
    
    return {
        'message': 'CSV文件导入成功',
        'importedCount': processed_count,
        'totalCount': total_count,
        'historyId': import_history.id
    }


def _sanitize_input(input_str):
    """
    清理输入字符串，移除潜在的危险字符
    
    Args:
        input_str: 输入字符串
    
    Returns:
        str: 清理后的字符串
    """
    if not input_str:
        return ''
    
    # 移除潜在的危险字符和脚本标签
    import re
    # 移除潜在的恶意内容
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', input_str, flags=re.IGNORECASE|re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'vbscript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)  # 移除事件处理器
    
    # 返回清理后的字符串，防止其他类型的注入
    return sanitized.strip()


def validate_csv_headers(file_path):
    """
    验证CSV文件的列头是否符合要求
    
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
        return {
            'valid': False,
            'message': '无法识别文件编码，请确保文件为文本格式',
            'headers': []
        }
    
    # 使用StringIO和检测到的编码来处理CSV
    import io
    file_io = io.StringIO(file_content)
    
    # 检测CSV格式
    sample = file_content[:1024]
    sniffer = csv.Sniffer()
    delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
    
    reader = csv.DictReader(file_io, delimiter=delimiter)
    headers = [h.strip().lower() for h in reader.fieldnames]  # 转换为小写进行比较

    
    # 检查是否包含必需的列
    missing_required = []
    for group in required_headers:
        found = any(h in headers for h in group)
        if not found:
            missing_required.append(' 或 '.join(group))
    
    if missing_required:
        return {
            'valid': False,
            'message': f'缺少必需的列: {", ".join(missing_required)}',
            'headers': headers
        }
    
    return {
        'valid': True,
        'message': 'CSV文件格式验证通过',
        'headers': headers
    }