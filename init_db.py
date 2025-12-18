"""
数据库初始化脚本
用于创建数据库表和插入初始数据
"""

from app import app, db
from models import EquipmentType, ProblemCategory, SolutionCategory, SystemConfig


def init_database():
    """初始化数据库表和初始数据"""
    with app.app_context():
        # 创建所有表
        print("创建数据库表...")
        db.create_all()
        print("数据库表创建完成")
        
        # 检查是否已有设备类型数据，避免重复插入
        if EquipmentType.query.count() == 0:
            print("插入初始设备类型数据...")
            equipment_types = [
                EquipmentType(name='电子设备', description='各类电子类产品'),
                EquipmentType(name='机械设备', description='各类机械装置'),
                EquipmentType(name='软件系统', description='各类软件应用'),
                EquipmentType(name='网络设备', description='网络相关硬件'),
                EquipmentType(name='测试设备', description='测试测量仪器'),
            ]
            for et in equipment_types:
                db.session.add(et)
            db.session.commit()
            print("设备类型数据插入完成")
        else:
            print("设备类型数据已存在，跳过插入")
        
        # 检查是否已有问题分类数据，避免重复插入
        if ProblemCategory.query.count() == 0:
            print("插入初始问题分类数据...")
            problem_categories = [
                ProblemCategory(name='设计缺陷', description='产品设计阶段存在的问题'),
                ProblemCategory(name='制造缺陷', description='生产制造过程中产生的问题'),
                ProblemCategory(name='材料问题', description='材料选择或质量问题'),
                ProblemCategory(name='工艺问题', description='生产工艺相关问题'),
                ProblemCategory(name='使用不当', description='用户使用不当造成的问题'),
                ProblemCategory(name='维护不足', description='维护保养不当造成的问题'),
                ProblemCategory(name='环境因素', description='环境条件影响造成的问题'),
                ProblemCategory(name='兼容性问题', description='与其他系统或设备兼容性问题'),
            ]
            for pc in problem_categories:
                db.session.add(pc)
            db.session.commit()
            print("问题分类数据插入完成")
        else:
            print("问题分类数据已存在，跳过插入")
        
        # 检查是否已有解决方案分类数据，避免重复插入
        if SolutionCategory.query.count() == 0:
            print("插入初始解决方案分类数据...")
            solution_categories = [
                SolutionCategory(name='设计优化', description='通过设计改进解决问题'),
                SolutionCategory(name='工艺改进', description='通过改进生产工艺解决问题'),
                SolutionCategory(name='材料更换', description='更换更合适的材料'),
                SolutionCategory(name='使用培训', description='对用户进行使用培训'),
                SolutionCategory(name='维护规范', description='制定维护保养规范'),
                SolutionCategory(name='防护措施', description='增加防护措施'),
                SolutionCategory(name='软件更新', description='通过软件更新解决问题'),
                SolutionCategory(name='硬件升级', description='通过硬件升级解决问题'),
            ]
            for sc in solution_categories:
                db.session.add(sc)
            db.session.commit()
            print("解决方案分类数据插入完成")
        else:
            print("解决方案分类数据已存在，跳过插入")
        
        # 检查是否已有系统配置数据，避免重复插入
        if SystemConfig.query.count() == 0:
            print("插入初始系统配置数据...")
            system_configs = [
                SystemConfig(
                    config_key='ai_model_endpoint',
                    config_value='https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                    description='AI模型API端点'
                ),
                SystemConfig(
                    config_key='ai_model_name',
                    config_value='qwen-max',
                    description='使用的AI模型名称'
                ),
                SystemConfig(
                    config_key='ai_temperature',
                    config_value='0.7',
                    description='AI生成温度参数'
                ),
                SystemConfig(
                    config_key='default_import_batch_size',
                    config_value='100',
                    description='默认导入批次大小'
                ),
                SystemConfig(
                    config_key='auto_analysis_enabled',
                    config_value='true',
                    description='是否启用自动AI分析'
                ),
            ]
            for sc in system_configs:
                db.session.add(sc)
            db.session.commit()
            print("系统配置数据插入完成")
        else:
            print("系统配置数据已存在，跳过插入")
        
        print("数据库初始化完成！")


def reset_database():
    """重置数据库 - 仅用于开发环境"""
    with app.app_context():
        print("删除所有表...")
        db.drop_all()
        print("表已删除")
        
        # 重新初始化
        init_database()


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        print("正在重置数据库...")
        reset_database()
    else:
        print("正在初始化数据库...")
        init_database()