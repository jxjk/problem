"""
简化版应用启动脚本
绕过一些大型依赖，先启动基础功能
"""
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import json
import csv
from io import StringIO


# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-for-equipment-problem-tracker'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max file size

# 允许跨域请求
CORS(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 模拟数据库 - 使用简单的字典存储（生产环境应使用真正的数据库）
problems_db = []
equipment_types_db = [
    {'id': 1, 'name': '服务器', 'description': '服务器设备'},
    {'id': 2, 'name': '网络设备', 'description': '路由器、交换机等网络设备'},
    {'id': 3, 'name': '存储设备', 'description': '硬盘、SSD等存储设备'},
    {'id': 4, 'name': '终端设备', 'description': '电脑、手机等终端设备'},
    {'id': 5, 'name': '工业设备', 'description': '生产线设备'},
]
problem_categories_db = [
    {'id': 1, 'name': '设计缺陷', 'description': '设计阶段引入的问题'},
    {'id': 2, 'name': '制造缺陷', 'description': '制造过程中的问题'},
    {'id': 3, 'name': '材料问题', 'description': '材料本身或选择不当的问题'},
    {'id': 4, 'name': '工艺问题', 'description': '生产工艺相关的问题'},
    {'id': 5, 'name': '使用不当', 'description': '操作或使用方式不当导致的问题'},
]
solution_categories_db = [
    {'id': 1, 'name': '设计优化', 'description': '通过设计改进解决问题'},
    {'id': 2, 'name': '工艺改进', 'description': '通过工艺优化解决问题'},
    {'id': 3, 'name': '材料更换', 'description': '更换材料解决问题'},
    {'id': 4, 'name': '操作培训', 'description': '通过培训改进操作'},
    {'id': 5, 'name': '维护规范', 'description': '制定维护规范'},
]

# 模拟AI分析函数
def analyze_problem_with_ai(title, description):
    """模拟AI分析函数"""
    return {
        'analysis': f'基于问题"{title}"的分析：这是一个常见的设备问题，建议检查相关配置和环境条件。',
        'suggestions': ['检查设备配置', '验证环境条件', '审查操作流程']
    }

def extract_category_from_ai_response(ai_analysis, title, description):
    """从AI响应中提取分类信息"""
    return {
        'problem_category_id': 1,
        'solution_category_id': 1,
        'priority': 'medium'
    }

# 路由定义
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
    filtered_problems = problems_db
    
    # 添加过滤条件
    if status:
        filtered_problems = [p for p in filtered_problems if p.get('status') == status]
    if phase:
        filtered_problems = [p for p in filtered_problems if p.get('phase') == phase]
    if equipment_type:
        filtered_problems = [p for p in filtered_problems if str(p.get('equipment_type_id')) == equipment_type]
    
    # 分页
    start = (page - 1) * limit
    end = start + limit
    paginated_problems = filtered_problems[start:end]
    total = len(filtered_problems)
    
    result = []
    for problem in paginated_problems:
        problem_data = {
            'id': problem.get('id'),
            'title': problem.get('title'),
            'description': problem.get('description'),
            'equipment_type_id': problem.get('equipment_type_id'),
            'equipment_type_name': get_equipment_type_name(problem.get('equipment_type_id')),
            'problem_category_id': problem.get('problem_category_id'),
            'problem_category_name': get_problem_category_name(problem.get('problem_category_id')),
            'solution_category_id': problem.get('solution_category_id'),
            'solution_category_name': get_solution_category_name(problem.get('solution_category_id')),
            'status': problem.get('status'),
            'priority': problem.get('priority'),
            'phase': problem.get('phase'),
            'discovered_by': problem.get('discovered_by'),
            'discovered_at': problem.get('discovered_at'),
            'ai_analyzed': problem.get('ai_analyzed'),
            'ai_analysis': problem.get('ai_analysis'),
            'solution_description': problem.get('solution_description'),
            'created_at': problem.get('created_at'),
            'updated_at': problem.get('updated_at')
        }
        result.append(problem_data)
    
    return jsonify({
        'problems': result,
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit
    })

def get_equipment_type_name(equipment_type_id):
    """获取设备类型名称"""
    for et in equipment_types_db:
        if et['id'] == equipment_type_id:
            return et['name']
    return None

def get_problem_category_name(problem_category_id):
    """获取问题分类名称"""
    for cat in problem_categories_db:
        if cat['id'] == problem_category_id:
            return cat['name']
    return None

def get_solution_category_name(solution_category_id):
    """获取解决方案分类名称"""
    for cat in solution_categories_db:
        if cat['id'] == solution_category_id:
            return cat['name']
    return None

@app.route('/api/problems', methods=['POST'])
def create_problem():
    """创建新问题"""
    data = request.get_json()
    
    if not data.get('title') or not data.get('description'):
        return jsonify({'error': '标题和描述不能为空'}), 400
    
    # 创建问题记录
    problem_id = len(problems_db) + 1
    problem = {
        'id': problem_id,
        'title': data.get('title'),
        'description': data.get('description'),
        'equipment_type_id': data.get('equipment_type_id', 1),
        'problem_category_id': data.get('problem_category_id', 1),
        'solution_category_id': data.get('solution_category_id', 1),
        'status': data.get('status', 'new'),
        'priority': data.get('priority', 'medium'),
        'phase': data.get('phase', 'design'),
        'discovered_by': data.get('discovered_by', 'Unknown'),
        'discovered_at': data.get('discovered_at'),
        'ai_analyzed': False,
        'ai_analysis': None,
        'solution_description': data.get('solution_description', ''),
        'solution_implementation': data.get('solution_implementation'),
        'solution_verification': data.get('solution_verification'),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    problems_db.append(problem)
    
    # 模拟AI分析
    try:
        ai_result = analyze_problem_with_ai(problem['title'], problem['description'])
        problem['ai_analyzed'] = True
        problem['ai_analysis'] = ai_result.get('analysis', '')
        
        # 从AI响应中提取分类信息
        category_info = extract_category_from_ai_response(
            ai_result.get('analysis', ''), 
            problem['title'], 
            problem['description']
        )
        
        problem['problem_category_id'] = category_info.get('problem_category_id', 1)
        problem['solution_category_id'] = category_info.get('solution_category_id', 1)
        problem['priority'] = category_info.get('priority', 'medium')
    except Exception as e:
        print(f'AI分析失败: {str(e)}')
        # 即使AI分析失败，问题仍然被创建
    
    return jsonify({'id': problem['id'], 'message': '问题添加成功'})

@app.route('/api/equipment-types', methods=['GET'])
def get_equipment_types():
    """获取设备类型列表"""
    return jsonify(equipment_types_db)

@app.route('/api/problem-categories', methods=['GET'])
def get_problem_categories():
    """获取问题分类列表"""
    return jsonify(problem_categories_db)

@app.route('/api/solution-categories', methods=['GET'])
def get_solution_categories():
    """获取解决方案分类列表"""
    return jsonify(solution_categories_db)

@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计信息"""
    total_problems = len(problems_db)
    new_problems = len([p for p in problems_db if p.get('status') == 'new'])
    analyzed_problems = len([p for p in problems_db if p.get('status') == 'analyzed'])
    solved_problems = len([p for p in problems_db if p.get('status') == 'solved'])
    verified_problems = len([p for p in problems_db if p.get('status') == 'verified'])
    critical_problems = len([p for p in problems_db if p.get('priority') == 'critical'])
    design_phase_problems = len([p for p in problems_db if p.get('phase') == 'design'])
    development_phase_problems = len([p for p in problems_db if p.get('phase') == 'development'])
    usage_phase_problems = len([p for p in problems_db if p.get('phase') == 'usage'])
    maintenance_phase_problems = len([p for p in problems_db if p.get('phase') == 'maintenance'])
    
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

if __name__ == '__main__':
    print("正在启动设备问题追踪系统...")
    print("访问 http://localhost:5000 查看应用")
    app.run(debug=True, host='0.0.0.0', port=5000)