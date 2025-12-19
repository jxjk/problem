"""
数据库迁移脚本：为ImportHistory表添加failed_records字段
"""
from models import db, ImportHistory
from app import app

def migrate_import_history():
    with app.app_context():
        # 检查failed_records列是否存在，如果不存在则添加
        try:
            # 尝试添加failed_records列
            db.session.execute(
                db.text("ALTER TABLE import_history ADD COLUMN failed_records INTEGER DEFAULT 0")
            )
            db.session.commit()
            print("成功添加failed_records列到import_history表")
        except Exception as e:
            print(f"添加failed_records列时出错（可能已存在）: {e}")
            db.session.rollback()
        
        # 验证列是否存在
        try:
            result = db.session.execute(
                db.text("SELECT failed_records FROM import_history LIMIT 1")
            )
            print("验证成功：failed_records列存在")
        except Exception as e:
            print(f"验证失败：{e}")

if __name__ == "__main__":
    migrate_import_history()