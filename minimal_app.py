"""
最小化应用启动脚本
仅包含核心功能，无需外部依赖
"""
from flask import Flask, request, jsonify, render_template_string
import os
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-for-equipment-problem-tracker'

# 模拟数据库 - 使用简单的列表存储
problems_db = [
    {
        'id': 1,
        'title': '服务器过热问题',
        'description': '生产服务器在高负载时出现过热现象',
        'equipment_type_id': 1,
        'status': 'solved',
        'priority': 'high',
        'phase': 'usage',
        'created_at': '2023-01-15T10:30:00',
        'updated_at': '2023-01-15T15:45:00'
    },
    {
        'id': 2,
        'title': '网络延迟问题',
        'description': '网络设备在特定时段出现延迟增加',
        'equipment_type_id': 2,
        'status': 'analyzed',
        'priority': 'medium',
        'phase': 'development',
        'created_at': '2023-01-20T09:15:00',
        'updated_at': '2023-01-20T11:30:00'
    }
]

# 模拟设备类型数据
equipment_types = [
    {'id': 1, 'name': '服务器', 'description': '服务器设备'},
    {'id': 2, 'name': '网络设备', 'description': '路由器、交换机等网络设备'},
    {'id': 3, 'name': '存储设备', 'description': '硬盘、SSD等存储设备'},
]

@app.route('/')
def index():
    """主页 - 返回简单的HTML页面"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>设备问题追踪系统</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { color: #333; border-bottom: 2px solid #eee; padding-bottom: 20px; }
            .card { border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin: 10px 0; background-color: #f9f9f9; }
            .btn { background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; display: inline-block; margin: 5px; }
            .status-new { color: orange; }
            .status-analyzed { color: blue; }
            .status-solved { color: green; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>设备问题追踪系统</h1>
            <p>用于追踪和管理设备相关问题的系统</p>
        </div>
        
        <div>
            <h2>快速访问</h2>
            <a href="/api/problems" class="btn">查看所有问题</a>
            <a href="/api/equipment-types" class="btn">查看设备类型</a>
            <a href="/api/dashboard-stats" class="btn">查看统计信息</a>
        </div>
        
        <div>
            <h2>API端点</h2>
            <div class="card">
                <strong>GET /api/problems</strong> - 获取问题列表<br>
                <strong>POST /api/problems</strong> - 创建新问题<br>
                <strong>GET /api/equipment-types</strong> - 获取设备类型<br>
                <strong>GET /api/dashboard-stats</strong> - 获取统计信息
            </div>
        </div>
        
        <div>
            <h2>当前问题列表（示例）</h2>
            <div class="card">
                <p><strong>服务器过热问题</strong> (ID: 1)</p>
                <p>状态: <span class="status-solved">已解决</span> | 优先级: 高 | 阶段: 使用中</p>
                <p>描述: 生产服务器在高负载时出现过热现象</p>
            </div>
            <div class="card">
                <p><strong>网络延迟问题</strong> (ID: 2)</p>
                <p>状态: <span class="status-analyzed">已分析</span> | 优先级: 中 | 阶段: 开发</p>
                <p>描述: 网络设备在特定时段出现延迟增加</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/api/problems', methods=['GET'])
def get_problems():
    """获取问题列表"""
    return jsonify(problems_db)

@app.route('/api/equipment-types', methods=['GET'])
def get_equipment_types():
    """获取设备类型列表"""
    return jsonify(equipment_types)

@app.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计信息"""
    total_problems = len(problems_db)
    new_problems = len([p for p in problems_db if p.get('status') == 'new'])
    analyzed_problems = len([p for p in problems_db if p.get('status') == 'analyzed'])
    solved_problems = len([p for p in problems_db if p.get('status') == 'solved'])
    
    return jsonify({
        'total_problems': total_problems,
        'new_problems': new_problems,
        'analyzed_problems': analyzed_problems,
        'solved_problems': solved_problems
    })

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
        'status': data.get('status', 'new'),
        'priority': data.get('priority', 'medium'),
        'phase': data.get('phase', 'design'),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    problems_db.append(problem)
    
    return jsonify({'id': problem['id'], 'message': '问题添加成功'})

if __name__ == '__main__':
    print("正在启动最小化设备问题追踪系统...")
    print("访问 http://localhost:5000 查看应用")
    app.run(debug=True, host='0.0.0.0', port=5000)