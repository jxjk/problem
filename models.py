from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class EquipmentType(db.Model):
    """设备类型表"""
    __tablename__ = 'equipment_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 与问题表的关系
    problems = db.relationship('Problem', backref='equipment_type', lazy=True)
    
    def __repr__(self):
        return f'<EquipmentType {self.name}>'


class ProblemCategory(db.Model):
    """问题分类表"""
    __tablename__ = 'problem_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('problem_categories.id'))
    
    # 与问题表的关系
    problems = db.relationship('Problem', backref='problem_category', lazy=True)
    
    def __repr__(self):
        return f'<ProblemCategory {self.name}>'


class SolutionCategory(db.Model):
    """解决方案分类表"""
    __tablename__ = 'solution_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # 与问题表的关系
    problems = db.relationship('Problem', backref='solution_category', lazy=True)
    
    def __repr__(self):
        return f'<SolutionCategory {self.name}>'


class Problem(db.Model):
    """问题点主表"""
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)  # 问题标题
    description = db.Column(db.Text)  # 问题描述
    equipment_type_id = db.Column(db.Integer, db.ForeignKey('equipment_types.id'))  # 设备类型ID
    problem_category_id = db.Column(db.Integer, db.ForeignKey('problem_categories.id'))  # 问题分类ID
    solution_category_id = db.Column(db.Integer, db.ForeignKey('solution_categories.id'))  # 解决方案分类ID
    status = db.Column(db.Enum('new', 'analyzed', 'solved', 'verified', name='problem_status'), default='new')  # 问题状态
    priority = db.Column(db.Enum('low', 'medium', 'high', 'critical', name='problem_priority'), default='medium')  # 优先级
    phase = db.Column(db.Enum('design', 'development', 'usage', 'maintenance', name='problem_phase'), nullable=False)  # 发现阶段
    discovered_by = db.Column(db.String(100))  # 发现者
    discovered_at = db.Column(db.Date)  # 发现时间
    ai_analyzed = db.Column(db.Boolean, default=False)  # 是否已AI分析
    ai_analysis = db.Column(db.Text)  # AI分析结果
    solution_description = db.Column(db.Text)  # 解决方案描述
    solution_implementation = db.Column(db.Text)  # 解决方案实施
    solution_verification = db.Column(db.Text)  # 解决方案验证
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    
    def __repr__(self):
        return f'<Problem {self.title}>'


class AIAnalysisHistory(db.Model):
    """AI分析历史表"""
    __tablename__ = 'ai_analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    analysis_type = db.Column(db.Enum('categorization', 'solution_suggestion', 'risk_assessment', name='analysis_type'), nullable=False)
    original_content = db.Column(db.Text)  # 原始内容
    ai_response = db.Column(db.Text)  # AI响应
    confidence_score = db.Column(db.Float)  # 置信度
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)  # 分析时间
    
    # 与问题表的关系
    problem = db.relationship('Problem', backref='ai_analysis_history', lazy=True)
    
    def __repr__(self):
        return f'<AIAnalysisHistory {self.analysis_type}>'


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'engineer', 'analyst', 'viewer', name='user_role'), default='engineer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'


class ImportHistory(db.Model):
    """问题导入历史表"""
    __tablename__ = 'import_history'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 导入者
    total_records = db.Column(db.Integer)  # 总记录数
    processed_records = db.Column(db.Integer)  # 处理记录数
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed', name='import_status'), default='pending')
    started_at = db.Column(db.DateTime)  # 开始时间
    completed_at = db.Column(db.DateTime)  # 完成时间
    error_log = db.Column(db.Text)  # 错误日志
    
    def __repr__(self):
        return f'<ImportHistory {self.filename}>'


class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)  # 配置键
    config_value = db.Column(db.Text)  # 配置值
    description = db.Column(db.Text)  # 描述
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    
    def __repr__(self):
        return f'<SystemConfig {self.config_key}>'