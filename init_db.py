"""
初始化数据库
创建所有表并添加初始数据
"""
from models import db, EquipmentType, ProblemCategory, SolutionCategory
from run import app  # 从run.py导入app
from vector_db import init_vector_db


def init_database():
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        # 添加默认设备类型
        if not EquipmentType.query.first():
            default_equipment_types = [
                {'name': '服务器', 'description': '服务器设备'},
                {'name': '网络设备', 'description': '路由器、交换机等网络设备'},
                {'name': '存储设备', 'description': '硬盘、SSD等存储设备'},
                {'name': '终端设备', 'description': '电脑、手机等终端设备'},
                {'name': '工业设备', 'description': '生产线设备'},
            ]
            for item in default_equipment_types:
                equipment_type = EquipmentType(name=item['name'], description=item['description'])
                db.session.add(equipment_type)
        
        # 添加默认问题分类
        if not ProblemCategory.query.first():
            default_problem_categories = [
                {'name': '设计缺陷', 'description': '设计阶段引入的问题'},
                {'name': '制造缺陷', 'description': '制造过程中的问题'},
                {'name': '材料问题', 'description': '材料本身或选择不当的问题'},
                {'name': '工艺问题', 'description': '生产工艺相关的问题'},
                {'name': '使用不当', 'description': '操作或使用方式不当导致的问题'},
                {'name': '维护不足', 'description': '维护保养不到位导致的问题'},
                {'name': '环境因素', 'description': '环境条件导致的问题'},
                {'name': '兼容性问题', 'description': '与其他设备或系统兼容性问题'},
            ]
            for item in default_problem_categories:
                category = ProblemCategory(name=item['name'], description=item['description'])
                db.session.add(category)
        
        # 添加默认解决方案分类
        if not SolutionCategory.query.first():
            default_solution_categories = [
                {'name': '设计优化', 'description': '通过设计改进解决问题'},
                {'name': '工艺改进', 'description': '通过工艺优化解决问题'},
                {'name': '材料更换', 'description': '更换材料解决问题'},
                {'name': '操作培训', 'description': '通过培训改进操作'},
                {'name': '维护规范', 'description': '制定维护规范'},
                {'name': '防护措施', 'description': '增加防护措施'},
                {'name': '软件更新', 'description': '通过软件更新解决问题'},
                {'name': '硬件升级', 'description': '通过硬件升级解决问题'},
            ]
            for item in default_solution_categories:
                category = SolutionCategory(name=item['name'], description=item['description'])
                db.session.add(category)
        
        # 提交所有更改
        db.session.commit()
        
        # 初始化向量数据库
        init_vector_db()
        print("向量数据库初始化完成！")
        
        print("数据库初始化完成！")


if __name__ == '__main__':
    init_database()