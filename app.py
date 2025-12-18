from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
import csv
from io import StringIO

from models import db, Problem, EquipmentType, ProblemCategory, SolutionCategory
from config import Config
from csv_import import import_csv_file
from ai_analysis import analyze_problem_with_ai, extract_category_from_ai_response
from vector_db import init_vector_db

app = Flask(__name__)
app.config.from_object(Config)

# 允许跨域请求
CORS(app)

# 初始化数据库
db.init_app(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页 - 显示仪表盘"""
    return render_template('dashboard.html')


@app.route('/api/problems', methods=['GET'])
def get_problems():
    """获取问题列表"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    status = request.args.get('status')
    phase = request.args.get('phase')
    equipment_type = request.args.get('equipment_type')

    # 基础查询
    query = db.session.query(Problem).join(EquipmentType, isouter=True).join(ProblemCategory, isouter=True)
    
    # 添加过滤条件
    if status:
        query = query.filter(Problem.status == status)
    if phase:
        query = query.filter(Problem.phase == phase)
    if equipment_type:
        query = query.filter(Problem.equipment_type_id == equipment_type)
    
    # 分页
    total = query.count()
    problems = query.order_by(Problem.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    result = []
    for problem in problems:
        problem_data = {
            'id': problem.id,
            'title': problem.title,
            'description': problem.description,
            'equipment_type_id': problem.equipment_type_id,
            'equipment_type_name': problem.equipment_type.name if problem.equipment_type else None,
            'problem_category_id': problem.problem_category_id,
            'problem_category_name': problem.problem_category.name if problem.problem_category else None,
            'solution_category_id': problem.solution_category_id,
            'solution_category_name': problem.solution_category.name if problem.solution_category else None,
            'status': problem.status,
            'priority': problem.priority,
            'phase': problem.phase,
            'discovered_by': problem.discovered_by,
            'discovered_at': problem.discovered_at.isoformat() if problem.discovered_at else None,
            'ai_analyzed': problem.ai_analyzed,
            'ai_analysis': problem.ai_analysis,
            'solution_description': problem.solution_description,
            'created_at': problem.created_at.isoformat(),
            'updated_at': problem.updated_at.isoformat()
        }
        result.append(problem_data)
    
    return jsonify({
        'problems': result,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    })


@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """获取问题详情"""
    problem = Problem.query.get_or_404(problem_id)
    
    problem_data = {
        'id': problem.id,
        'title': problem.title,
        'description': problem.description,
        'equipment_type_id': problem.equipment_type_id,
        'equipment_type_name': problem.equipment_type.name if problem.equipment_type else None,
        'problem_category_id': problem.problem_category_id,
        'problem_category_name': problem.problem_category.name if problem.problem_category else None,
        'solution_category_id': problem.solution_category_id,
        'solution_category_name': problem.solution_category.name if problem.solution_category else None,
        'status': problem.status,
        'priority': problem.priority,
        'phase': problem.phase,
        'discovered_by': problem.discovered_by,
        'discovered_at': problem.discovered_at.isoformat() if problem.discovered_at else None,
        'ai_analyzed': problem.ai_analyzed,
        'ai_analysis': problem.ai_analysis,
        'solution_description': problem.solution_description,
        'solution_implementation': problem.solution_implementation,
        'solution_verification': problem.solution_verification,
        'created_at': problem.created_at.isoformat(),
        'updated_at': problem.updated_at.isoformat()
    }
    
    return jsonify(problem_data)


@app.route('/api/problems', methods=['POST'])
def create_problem():
    """创建新问题"""
    data = request.get_json()
    
    if not data.get('title') or not data.get('description'):
        return jsonify({'error': '标题和描述不能为空'}), 400
    
    # 创建问题记录
    problem = Problem(
        title=data.get('title'),
        description=data.get('description'),
        equipment_type_id=data.get('equipment_type_id'),
        phase=data.get('phase', 'design'),
        discovered_by=data.get('discovered_by'),
        discovered_at=data.get('discovered_at')
    )
    
    db.session.add(problem)
    db.session.commit()
    
    # 触发AI分析
    try:
        ai_result = analyze_problem_with_ai(problem.title, problem.description)
        problem.ai_analyzed = True
        problem.ai_analysis = ai_result.get('analysis', '')
        
        # 从AI响应中提取分类信息
        category_info = extract_category_from_ai_response(
            ai_result.get('analysis', ''), 
            problem.title, 
            problem.description
        )
        
        problem.problem_category_id = category_info.get('problem_category_id', 1)
        problem.solution_category_id = category_info.get('solution_category_id', 1)
        problem.priority = category_info.get('priority', 'medium')
        
        db.session.commit()
    except Exception as e:
        app.logger.error(f'AI分析失败: {str(e)}')
        # 即使AI分析失败，问题仍然被创建
    
    # 将问题添加到向量数据库
    try:
        success = problem.save_to_vector_db()
        if not success:
            app.logger.error(f"无法将问题 {problem.id} 保存到向量数据库")
    except Exception as e:
        app.logger.error(f"保存问题到向量数据库失败: {str(e)}")
    
    return jsonify({'id': problem.id, 'message': '问题添加成功'})


@app.route('/api/equipment-types', methods=['GET'])
def get_equipment_types():
    """获取设备类型列表"""
    equipment_types = EquipmentType.query.all()
    result = []
    for et in equipment_types:
        result.append({
            'id': et.id,
            'name': et.name,
            'description': et.description
        })
    return jsonify(result)


@app.route('/api/problem-categories', methods=['GET'])
def get_problem_categories():
    """获取问题分类列表"""
    categories = ProblemCategory.query.all()
    result = []
    for cat in categories:
        result.append({
            'id': cat.id,
            'name': cat.name,
            'description': cat.description
        })
    return jsonify(result)


@app.route('/api/solution-categories', methods=['GET'])
def get_solution_categories():
    """获取解决方案分类列表"""
    categories = SolutionCategory.query.all()
    result = []
    for cat in categories:
        result.append({
            'id': cat.id,
            'name': cat.name,
            'description': cat.description
        })
    return jsonify(result)


@app.route('/api/import-csv', methods=['POST'])
def import_csv():
    """上传并导入CSV文件"""
    if 'csvFile' not in request.files:
        return jsonify({'error': '请上传CSV文件'}), 400
    
    file = request.files['csvFile']
    if file.filename == '':
        return jsonify({'error': '请上传CSV文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '只允许上传CSV文件'}), 400
    
    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 导入CSV数据
        result = import_csv_file(file_path)
        
        # 删除临时文件
        os.remove(file_path)
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f'CSV导入失败: {str(e)}')
        return jsonify({'error': '导入CSV文件失败', 'details': str(e)}), 500


@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计信息"""
    total_problems = Problem.query.count()
    new_problems = Problem.query.filter_by(status='new').count()
    analyzed_problems = Problem.query.filter_by(status='analyzed').count()
    solved_problems = Problem.query.filter_by(status='solved').count()
    verified_problems = Problem.query.filter_by(status='verified').count()
    critical_problems = Problem.query.filter_by(priority='critical').count()
    design_phase_problems = Problem.query.filter_by(phase='design').count()
    development_phase_problems = Problem.query.filter_by(phase='development').count()
    usage_phase_problems = Problem.query.filter_by(phase='usage').count()
    maintenance_phase_problems = Problem.query.filter_by(phase='maintenance').count()
    
    return jsonify({
        'total_problems': total_problems,
        'new_problems': new_problems,
        'analyzed_problems': analyzed_problems,
        'solved_problems': solved_problems,
        'verified_problems': verified_problems,
        'critical_problems': critical_problems,
        'design_phase_problems': design_phase_problems,
        'development_phase_problems': development_phase_problems,
        'usage_phase_problems': usage_phase_problems,
        'maintenance_phase_problems': maintenance_phase_problems
    })


@app.route('/api/problems-by-equipment', methods=['GET'])
def get_problems_by_equipment():
    """获取按设备类型统计的问题"""
    from sqlalchemy import func
    
    result = db.session.query(
        EquipmentType.name.label('equipment_type'),
        func.count(Problem.id).label('problem_count')
    ).outerjoin(Problem, EquipmentType.id == Problem.equipment_type_id)\
     .group_by(EquipmentType.id, EquipmentType.name)\
     .order_by(func.count(Problem.id).desc())\
     .all()
    
    return jsonify([{
        'equipment_type': row.equipment_type,
        'problem_count': row.problem_count
    } for row in result])


@app.route('/api/problems-by-category', methods=['GET'])
def get_problems_by_category():
    """获取按问题分类统计的问题"""
    from sqlalchemy import func
    
    result = db.session.query(
        ProblemCategory.name.label('category_name'),
        func.count(Problem.id).label('problem_count')
    ).outerjoin(Problem, ProblemCategory.id == Problem.problem_category_id)\
     .group_by(ProblemCategory.id, ProblemCategory.name)\
     .order_by(func.count(Problem.id).desc())\
     .all()
    
    return jsonify([{
        'category_name': row.category_name,
        'problem_count': row.problem_count
    } for row in result])


@app.route('/api/ai-query', methods=['POST'])
def ai_query():
    """AI智能查询接口 - 用于规避设计缺陷"""
    data = request.get_json()
    query_text = data.get('query')
    
    if not query_text:
        return jsonify({'error': '查询内容不能为空'}), 400
    
    try:
        from sqlalchemy import desc
        
        # 从数据库获取相关问题数据
        problems = Problem.query.filter(
            Problem.status.in_(['solved', 'verified'])
        ).order_by(desc(Problem.created_at)).limit(20).all()
        
        # 构建AI查询提示
        problems_text = ""
        for p in problems:
            problems_text += f"""
问题: {p.title}
描述: {p.description}
AI分析: {p.ai_analysis or '未分析'}
解决方案: {p.solution_description or '无'}
发现阶段: {p.phase}
"""

        prompt = f"""您是一个专业的设备设计顾问，帮助工程师在设计阶段规避潜在问题。基于以下历史问题数据库，请分析用户的设计查询。

历史问题数据：
{problems_text}

用户查询: "{query_text}"

请提供以下内容：
1. 是否存在类似的历史问题
2. 如果存在，这些问题的根本原因是什么
3. 如何在当前设计中避免这些问题
4. 具体的设计建议和最佳实践
5. 需要特别注意的关键点

请提供详细、专业的建议，帮助用户在设计阶段规避潜在问题。"""
        
        # 这里需要实现AI调用逻辑
        from openai import OpenAI  # 如果使用OpenAI
        import os
        
        # 可以根据配置使用不同的AI服务，这里暂时返回模拟响应
        ai_response = f"基于历史数据分析，针对您的查询 '{query_text}'，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"
        
        return jsonify({
            'query': query_text,
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f'AI查询失败: {str(e)}')
        return jsonify({'error': 'AI查询失败', 'details': str(e)}), 500


@app.route('/api/design-ai-suggestions', methods=['GET'])
def get_design_ai_suggestions():
    """获取AI建议用于设计阶段的接口"""
    try:
        from sqlalchemy import desc, func
        
        # 获取最常见的问题类型和相应的设计建议
        suggestions = db.session.query(
            ProblemCategory.name.label('category_name'),
            Problem.description,
            Problem.ai_analysis,
            Problem.solution_description,
            func.count(Problem.id).label('frequency')
        ).join(Problem, ProblemCategory.id == Problem.problem_category_id)\
         .filter(
             Problem.status.in_(['solved', 'verified']),
             Problem.phase == 'design'
         ).group_by(Problem.problem_category_id, ProblemCategory.name, Problem.description, Problem.ai_analysis, Problem.solution_description)\
         .order_by(func.count(Problem.id).desc())\
         .limit(10).all()
        
        result = []
        for suggestion in suggestions:
            result.append({
                'category_name': suggestion.category_name,
                'description': suggestion.description,
                'ai_analysis': suggestion.ai_analysis,
                'solution_description': suggestion.solution_description,
                'frequency': suggestion.frequency
            })
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f'获取设计AI建议失败: {str(e)}')
        return jsonify({'error': '获取设计AI建议失败'}), 500


# 添加路由以提供静态页面
@app.route('/problems')
def problems_page():
    """问题列表页面"""
    return render_template('problems.html')


@app.route('/add-problem')
def add_problem_page():
    """添加问题页面"""
    return render_template('add_problem.html')


@app.route('/import-csv')
def import_csv_page():
    """CSV导入页面"""
    return render_template('import_csv.html')


@app.route('/dashboard')
def dashboard_page():
    """仪表盘页面"""
    return render_template('dashboard.html')


@app.before_first_request
def initialize_vector_db():
    """
    在第一次请求前初始化向量数据库
    将现有问题数据添加到向量数据库中
    """
    init_vector_db()
    
    # 将现有的问题导入到向量数据库中
    try:
        existing_problems = Problem.query.all()
        app.logger.info(f"开始同步 {len(existing_problems)} 个现有问题到向量数据库")
        
        # 批量处理现有问题
        problems_data = []
        for problem in existing_problems:
            metadata = {
                'equipment_type_id': problem.equipment_type_id,
                'problem_category_id': problem.problem_category_id,
                'solution_category_id': problem.solution_category_id,
                'status': problem.status,
                'priority': problem.priority,
                'phase': problem.phase,
                'discovered_by': problem.discovered_by,
                'discovered_at': str(problem.discovered_at) if problem.discovered_at else None,
                'ai_analyzed': problem.ai_analyzed,
                'ai_analysis': problem.ai_analysis,
                'solution_description': problem.solution_description,
                'created_at': str(problem.created_at),
                'updated_at': str(problem.updated_at)
            }
            problems_data.append({
                'id': str(problem.id),
                'title': problem.title,
                'description': problem.description or "",
                'metadata': metadata
            })
        
        if problems_data:
            from vector_db import get_vector_db
            vector_db = get_vector_db()
            result = vector_db.batch_add_problems(problems_data)
            app.logger.info(f"批量同步完成: 成功 {result['success_count']} 个, 失败 {len(result['failed_ids'])} 个")
            
            if result['failed_ids']:
                app.logger.error(f"以下问题同步失败: {result['failed_ids']}")
    except Exception as e:
        app.logger.error(f"同步现有问题到向量数据库时出错: {str(e)}")


@app.route('/api/search-similar-problems', methods=['POST'])
def search_similar_problems():
    """搜索相似问题 - 使用向量数据库"""
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': '查询内容不能为空'}), 400
    
    try:
        # 使用向量数据库搜索相似问题
        similar_problems = Problem.search_similar_problems(query, n_results=10)
        
        # 获取对应的数据库问题信息
        detailed_results = []
        for result in similar_problems:
            problem_id = result['id']
            problem = Problem.query.get(problem_id)
            if problem:
                problem_data = {
                    'id': problem.id,
                    'title': problem.title,
                    'description': problem.description,
                    'equipment_type_name': problem.equipment_type.name if problem.equipment_type else None,
                    'problem_category_name': problem.problem_category.name if problem.problem_category else None,
                    'solution_category_name': problem.solution_category.name if problem.solution_category else None,
                    'status': problem.status,
                    'priority': problem.priority,
                    'phase': problem.phase,
                    'distance': result.get('distance'),  # 相似度距离
                    'similarity_score': 1 - result.get('distance', 0)  # 转换为相似度分数
                }
                detailed_results.append(problem_data)
        
        return jsonify({
            'query': query,
            'similar_problems': detailed_results,
            'count': len(detailed_results)
        })
    except Exception as e:
        app.logger.error(f'搜索相似问题失败: {str(e)}')
        return jsonify({'error': '搜索相似问题失败', 'details': str(e)}), 500





@app.route('/api/problems/<int:problem_id>', methods=['PUT'])
def update_problem(problem_id):
    """更新问题"""
    problem = Problem.query.get_or_404(problem_id)
    data = request.get_json()
    
    # 更新字段
    if 'title' in data:
        problem.title = data['title']
    if 'description' in data:
        problem.description = data['description']
    if 'equipment_type_id' in data:
        problem.equipment_type_id = data['equipment_type_id']
    if 'problem_category_id' in data:
        problem.problem_category_id = data['problem_category_id']
    if 'solution_category_id' in data:
        problem.solution_category_id = data['solution_category_id']
    if 'status' in data:
        problem.status = data['status']
    if 'priority' in data:
        problem.priority = data['priority']
    if 'phase' in data:
        problem.phase = data['phase']
    if 'discovered_by' in data:
        problem.discovered_by = data['discovered_by']
    if 'discovered_at' in data:
        problem.discovered_at = data['discovered_at']
    if 'ai_analysis' in data:
        problem.ai_analysis = data['ai_analysis']
    if 'solution_description' in data:
        problem.solution_description = data['solution_description']
    if 'solution_implementation' in data:
        problem.solution_implementation = data['solution_implementation']
    if 'solution_verification' in data:
        problem.solution_verification = data['solution_verification']
    
    problem.updated_at = datetime.utcnow()
    db.session.commit()
    
    # 更新向量数据库中的问题
    try:
        success = problem.update_vector_db()
        if not success:
            app.logger.error(f"无法更新向量数据库中的问题 {problem.id}")
    except Exception as e:
        app.logger.error(f"更新向量数据库失败: {str(e)}")
    
    return jsonify({'id': problem.id, 'message': '问题更新成功'})


@app.route('/api/problems/<int:problem_id>', methods=['DELETE'])
def delete_problem(problem_id):
    """删除问题"""
    problem = Problem.query.get_or_404(problem_id)
    
    db.session.delete(problem)
    db.session.commit()
    
    # 从向量数据库中删除问题
    try:
        success = problem.delete_from_vector_db()
        if not success:
            app.logger.error(f"无法从向量数据库中删除问题 {problem.id}")
    except Exception as e:
        app.logger.error(f"从向量数据库删除问题失败: {str(e)}")
    
    return jsonify({'message': '问题删除成功'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # 初始化向量数据库
        init_vector_db()
        
        # 将现有问题导入到向量数据库中
        try:
            existing_problems = Problem.query.all()
            app.logger.info(f"开始同步 {len(existing_problems)} 个现有问题到向量数据库")
            
            # 批量处理现有问题
            problems_data = []
            for problem in existing_problems:
                metadata = {
                    'equipment_type_id': problem.equipment_type_id,
                    'problem_category_id': problem.problem_category_id,
                    'solution_category_id': problem.solution_category_id,
                    'status': problem.status,
                    'priority': problem.priority,
                    'phase': problem.phase,
                    'discovered_by': problem.discovered_by,
                    'discovered_at': str(problem.discovered_at) if problem.discovered_at else None,
                    'ai_analyzed': problem.ai_analyzed,
                    'ai_analysis': problem.ai_analysis,
                    'solution_description': problem.solution_description,
                    'created_at': str(problem.created_at),
                    'updated_at': str(problem.updated_at)
                }
                problems_data.append({
                    'id': str(problem.id),
                    'title': problem.title,
                    'description': problem.description or "",
                    'metadata': metadata
                })
            
            if problems_data:
                from vector_db import get_vector_db
                vector_db = get_vector_db()
                result = vector_db.batch_add_problems(problems_data)
                app.logger.info(f"批量同步完成: 成功 {result['success_count']} 个, 失败 {len(result['failed_ids'])} 个")
                
                if result['failed_ids']:
                    app.logger.error(f"以下问题同步失败: {result['failed_ids']}")
        except Exception as e:
            app.logger.error(f"同步现有问题到向量数据库时出错: {str(e)}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)