-- 数据库初始化脚本
-- 创建数据库和表结构

-- 如果使用MySQL，可以使用以下命令创建数据库
-- CREATE DATABASE IF NOT EXISTS wenti_ji_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE wenti_ji_db;

-- 初始化设备类型数据
INSERT INTO equipment_types (name, description) VALUES
('电子设备', '各类电子类产品'),
('机械设备', '各类机械装置'),
('软件系统', '各类软件应用'),
('网络设备', '网络相关硬件'),
('测试设备', '测试测量仪器')
ON DUPLICATE KEY UPDATE name=name;

-- 初始化问题分类数据
INSERT INTO problem_categories (name, description) VALUES
('设计缺陷', '产品设计阶段存在的问题'),
('制造缺陷', '生产制造过程中产生的问题'),
('材料问题', '材料选择或质量问题'),
('工艺问题', '生产工艺相关问题'),
('使用不当', '用户使用不当造成的问题'),
('维护不足', '维护保养不当造成的问题'),
('环境因素', '环境条件影响造成的问题'),
('兼容性问题', '与其他系统或设备兼容性问题')
ON DUPLICATE KEY UPDATE name=name;

-- 初始化解决方案分类数据
INSERT INTO solution_categories (name, description) VALUES
('设计优化', '通过设计改进解决问题'),
('工艺改进', '通过改进生产工艺解决问题'),
('材料更换', '更换更合适的材料'),
('使用培训', '对用户进行使用培训'),
('维护规范', '制定维护保养规范'),
('防护措施', '增加防护措施'),
('软件更新', '通过软件更新解决问题'),
('硬件升级', '通过硬件升级解决问题')
ON DUPLICATE KEY UPDATE name=name;

-- 初始化系统配置数据
INSERT INTO system_config (config_key, config_value, description) VALUES
('ai_model_endpoint', 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation', 'AI模型API端点'),
('ai_model_name', 'qwen-max', '使用的AI模型名称'),
('ai_temperature', '0.7', 'AI生成温度参数'),
('default_import_batch_size', '100', '默认导入批次大小'),
('auto_analysis_enabled', 'true', '是否启用自动AI分析')
ON DUPLICATE KEY UPDATE config_key=config_key;