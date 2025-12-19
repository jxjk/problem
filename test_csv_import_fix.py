import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from csv_import import import_csv_file

def test_csv_import():
    """测试CSV导入功能"""
    with app.app_context():
        try:
            result = import_csv_file('D:\\Users\\00596\\Desktop\\wenTiJi\\testcsv\\sample1.csv')
            print('CSV导入成功:', result)
            return True
        except Exception as e:
            print('CSV导入失败:', str(e))
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_csv_import()