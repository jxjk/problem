"""
测试改进后的AI分析功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_analysis import analyze_problem_with_ai

def test_improved_ai_analysis():
    """测试改进后的AI分析功能"""
    print("测试改进后的AI分析功能...")
    
    # 测试用例1：普通设备问题
    title1 = "设备启动失败"
    description1 = "设备在启动过程中无法正常启动，电源指示灯闪烁。"
    equipment_type1 = "控制系统"
    phase1 = "使用"
    
    print(f"\n测试用例1:")
    print(f"标题: {title1}")
    print(f"描述: {description1}")
    print(f"设备类型: {equipment_type1}")
    print(f"发现阶段: {phase1}")
    
    result1 = analyze_problem_with_ai(title1, description1, equipment_type=equipment_type1, phase=phase1)
    print(f"AI分析结果:\n{result1['analysis']}")
    
    # 测试用例2：制造相关问题
    title2 = "零件尺寸偏差"
    description2 = "生产过程中发现零件尺寸超出公差范围。"
    equipment_type2 = "加工设备"
    phase2 = "制造"
    
    print(f"\n测试用例2:")
    print(f"标题: {title2}")
    print(f"描述: {description2}")
    print(f"设备类型: {equipment_type2}")
    print(f"发现阶段: {phase2}")
    
    result2 = analyze_problem_with_ai(title2, description2, equipment_type=equipment_type2, phase=phase2)
    print(f"AI分析结果:\n{result2['analysis']}")
    
    # 测试用例3：设计相关问题
    title3 = "散热不良"
    description3 = "设备在长时间运行后温度过高，导致自动保护停机。"
    equipment_type3 = "动力设备"
    phase3 = "设计"
    
    print(f"\n测试用例3:")
    print(f"标题: {title3}")
    print(f"描述: {description3}")
    print(f"设备类型: {equipment_type3}")
    print(f"发现阶段: {phase3}")
    
    result3 = analyze_problem_with_ai(title3, description3, equipment_type=equipment_type3, phase=phase3)
    print(f"AI分析结果:\n{result3['analysis']}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_improved_ai_analysis()