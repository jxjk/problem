import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_analysis import analyze_problem_with_ai, extract_category_from_ai_response

def test_ai_analysis():
    print("测试改进后的AI分析功能...")
    
    # 测试用例 1
    test_title = '设备过热问题'
    test_description = '设备在高负载运行时出现过热现象，导致自动停机'
    test_equipment = '工业电机'
    test_phase = '使用阶段'

    print(f"测试标题: {test_title}")
    print(f"测试描述: {test_description}")
    print(f"设备类型: {test_equipment}")
    print(f"发现阶段: {test_phase}")
    print("-" * 60)
    
    try:
        # 调用AI分析功能
        result = analyze_problem_with_ai(test_title, test_description, test_equipment, test_phase)
        print("AI分析结果:")
        print(result['analysis'])
        print("\n" + "="*60 + "\n")

        # 测试分类提取功能
        category_result = extract_category_from_ai_response(result['analysis'], test_title, test_description)
        print("分类提取结果:")
        print(f"问题分类ID: {category_result['problem_category_id']}")
        print(f"解决方案分类ID: {category_result['solution_category_id']}")
        print(f"优先级: {category_result['priority']}")
        print(f"置信度: {category_result['confidence']}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    # 测试用例 2 - 不同类型的问题
    print("\n" + "="*60)
    print("测试用例 2 - 设计缺陷问题")
    test_title2 = '产品设计缺陷'
    test_description2 = '产品在低温环境下无法正常启动，经分析发现电路设计未考虑低温影响'
    test_equipment2 = '电子控制模块'
    test_phase2 = '设计阶段'

    print(f"测试标题: {test_title2}")
    print(f"测试描述: {test_description2}")
    print(f"设备类型: {test_equipment2}")
    print(f"发现阶段: {test_phase2}")
    print("-" * 60)
    
    try:
        result2 = analyze_problem_with_ai(test_title2, test_description2, test_equipment2, test_phase2)
        print("AI分析结果:")
        print(result2['analysis'])
        print("\n" + "="*60 + "\n")

        # 测试分类提取功能
        category_result2 = extract_category_from_ai_response(result2['analysis'], test_title2, test_description2)
        print("分类提取结果:")
        print(f"问题分类ID: {category_result2['problem_category_id']}")
        print(f"解决方案分类ID: {category_result2['solution_category_id']}")
        print(f"优先级: {category_result2['priority']}")
        print(f"置信度: {category_result2['confidence']}")
        
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_analysis()