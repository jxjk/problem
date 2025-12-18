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
    从CSV文件导入问题数据
    
    Args:
        file_path: CSV文件路径
    
    Returns:
        dict: 包含导入结果的字典
    """
    results = []
    
    # 读取CSV文件
    with open(file_path, 'r', encoding='utf-8') as file:
        # 检测CSV格式
        sample = file.read(1024)
        file.seek(0)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
        
        reader = csv.DictReader(file, delimiter=delimiter)
        
        # 读取所有行
        for row in reader:
            results.append(row)
    
    if not results:
        return {'message': 'CSV文件为空', 'importedCount': 0, 'totalCount': 0}
    
    # 记录导入历史
    import_history = ImportHistory(
        filename=os.path.basename(file_path),
        imported_by=1,  # 默认用户ID
        total_records=len(results),
        status='processing',
        started_at=datetime.now()
    )
    db.session.add(import_history)
    db.session.flush()  # 获取ID但不提交
    
    processed_count = 0
    
    for row in results:
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
                
                db.session.commit()
            except Exception as e:
                print(f'AI分析失败: {str(e)}')
                # 即使AI分析失败也继续处理
                db.session.commit()
            
            processed_count += 1
            
        except Exception as e:
            print(f'处理CSV行时出错: {str(e)}')
            continue  # 继续处理下一行
    
    # 更新导入历史记录状态
    import_history.status = 'completed'
    import_history.processed_records = processed_count
    import_history.completed_at = datetime.now()
    
    db.session.commit()
    
    return {
        'message': 'CSV文件导入成功',
        'importedCount': processed_count,
        'totalCount': len(results),
        'historyId': import_history.id
    }


def validate_csv_headers(file_path):
    """
    验证CSV文件的列头是否符合要求
    
    Args:
        file_path: CSV文件路径
    
    Returns:
        dict: 包含验证结果的字典
    """
    required_headers = [
        ['title', 'problem', 'issue', '标题', '问题'],  # 至少包含其中之一
        ['description', 'reason', 'analysis', '描述', '原因', '分析']  # 至少包含其中之一
    ]
    
    with open(file_path, 'r', encoding='utf-8') as file:
        sample = file.read(1024)
        file.seek(0)
        sniffer = csv.Sniffer()
        delimiter = sniffer.sniff(sample).delimiter
        
        reader = csv.DictReader(file, delimiter=delimiter)
        headers = [h.strip() for h in reader.fieldnames]
    
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