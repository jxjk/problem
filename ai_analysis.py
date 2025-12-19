
"""
AI分析功能模块
处理问题的AI分析和分类
"""

import json
import re
from config import Config
import os
from vector_db import get_vector_db

# 根据配置决定使用哪种AI服务
def analyze_problem_with_ai(title, description, equipment_type=None, phase=None):
    """
    使用AI分析问题
    
    Args:
        title: 问题标题
        description: 问题描述
        equipment_type: 设备类型（可选）
        phase: 发现阶段（可选）
    
    Returns:
        dict: 包含AI分析结果的字典
    """
    try:
        # 构建AI提示
        equipment_context = f"设备类型: {equipment_type}" if equipment_type else "设备类型: 未指定"
        phase_context = f"发现阶段: {phase}" if phase else "发现阶段: 未指定"
        
        # 获取相似问题作为上下文
        similar_problems_context = ""
        try:
            similar_problems = get_similar_problems_by_vector(f"{title} {description}", top_k=3, min_similarity=0.3)
            if similar_problems:
                similar_problems_context = "\n相关历史问题:\n"
                for i, problem in enumerate(similar_problems[:3], 1):
                    metadata = problem.get('metadata', {})
                    similar_problems_context += f"{i}. {metadata.get('title', '未知标题')}: {metadata.get('description', '无描述')}\n"
        except:
            # 如果向量搜索失败，继续执行，不中断分析流程
            similar_problems_context = ""
        
        prompt = f"""请对以下设备问题进行深度分析，必须结合具体上下文信息进行分析：

{equipment_context}
{phase_context}
{similar_problems_context}
问题标题: {title}
问题描述: {description}

请严格按照以下框架进行深度分析，确保分析结果针对具体问题，避免模板化和千篇一律的描述：

1. 问题分类（从以下选项中选择最符合的一个）：
   - 设计缺陷：设计参数、设计标准、设计验证、设计假设等层面的问题
   - 制造缺陷：生产工艺、设备精度、操作规范等层面的问题
   - 材料问题：材料选择、材料质量、材料性能等层面的问题
   - 工艺问题：加工工艺、装配工艺、表面处理等层面的问题
   - 使用不当：操作错误、超负荷运行、违反使用规程等层面的问题
   - 维护不足：保养不及时、检修不彻底、维护方法不当等层面的问题
   - 环境因素：温度、湿度、腐蚀、振动、电磁干扰等外部环境问题
   - 兼容性问题：设备间兼容、系统兼容、接口兼容等层面的问题

2. 系统内部原因分析（必须针对具体问题进行深入分析，不能泛泛而谈）：
   - 设计层面：具体涉及哪些设计参数、设计标准、设计验证方法等
   - 制造层面：具体涉及哪些工艺参数、材料规格、生产流程、质量控制环节等
   - 维护层面：具体涉及哪些维护流程、维护标准、维护工具、维护周期等
   - 必须结合设备类型和问题的具体情况进行分析

3. 系统外部原因分析（必须针对具体问题进行深入分析，不能宽泛描述）：
   - 环境因素：具体环境参数（温度、湿度、振动、腐蚀性等）如何影响设备
   - 使用条件：具体操作方式、负载情况、使用频率、操作人员技能等如何导致问题
   - 外部干扰：具体干扰源（电磁干扰、物理冲击、化学腐蚀等）如何影响设备
   - 必须结合问题发现阶段和设备类型进行分析

4. 建议的解决方案（优先考虑内部原因的解决方案，提供具体实施步骤）：
   - 短期解决方案：立即可以实施的措施
   - 长期解决方案：根本性改进措施
   - 预防措施：避免类似问题再次发生的方法

5. 问题严重程度（低、中、高、严重）：
   - 低：轻微影响，可暂时忽略
   - 中：一定影响，需关注
   - 高：严重影响，需立即处理
   - 严重：可能导致严重后果，需紧急处理

6. 根本原因分析（深入分析问题的根本原因，而非表面现象）：
   - 从系统性角度分析根本原因
   - 考虑设计、制造、使用、维护等全生命周期因素
   - 结合相关历史问题进行关联分析

请确保每一项分析都与具体问题紧密相关，提供具体、可操作、有针对性的建议。"""
        
        # 根据配置使用不同的AI服务
        if Config.AI_PROVIDER == 'openai':
            return _analyze_with_openai(prompt, title, description, equipment_type, phase)
        elif Config.AI_PROVIDER == 'dashscope':  # 通义千问
            return _analyze_with_dashscope(prompt, title, description, equipment_type, phase)
        else:
            # 模拟AI响应（如果没有配置AI服务）
            return _simulate_ai_analysis(title, description, equipment_type, phase)
    
    except Exception as e:
        print(f'AI分析失败: {str(e)}')
        # 返回模拟分析结果以确保系统正常运行
        return _simulate_ai_analysis(title, description)


def _analyze_with_openai(prompt, title, description, equipment_type=None, phase=None):
    """使用OpenAI API进行分析"""
    try:
        import openai
        from config import Config
        
        openai.api_key = Config.OPENAI_API_KEY
        
        system_prompt = f"""你是一个专业的设备问题分析专家，帮助工程师分析设备问题并提供解决方案。请严格按照以下要求进行分析：

1. 针对性分析：根据具体问题进行深度分析，提供针对性的内部和外部原因分析
2. 避免模板化：避免使用通用模板，确保分析结果与具体问题相关
3. 结合上下文：分析时请结合设备类型、发现阶段等上下文信息
4. 结构化输出：按照指定框架提供分析结果
5. 具体化建议：提供具体、可操作的解决方案和建议

请确保分析结果具有专业性、针对性和实用性。"""
        
        response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=Config.AI_TEMPERATURE or 0.3
        )
        
        analysis = response.choices[0].message['content']
        return {'analysis': analysis}
    
    except ImportError:
        print("OpenAI\u5e93未安装，使用模拟分析")
        return _simulate_ai_analysis(title, description, equipment_type, phase)
    except Exception as e:
        print(f"OpenAI\u5206\u6790\u5931\u8d25: {str(e)}")
        return _simulate_ai_analysis(title, description, equipment_type, phase)


def _analyze_with_dashscope(prompt, title, description, equipment_type=None, phase=None):
    """使用通义千问API进行分析"""
    try:
        import requests
        from config import Config
        
        system_prompt = f"""你是一个专业的设备问题分析专家，帮助工程师分析设备问题并提供解决方案。请严格按照以下要求进行分析：

1. 针对性分析：根据具体问题进行深度分析，提供针对性的内部和外部原因分析
2. 避免模板化：避免使用通用模板，确保分析结果与具体问题相关
3. 结合上下文：分析时请结合设备类型、发现阶段等上下文信息
4. 结构化输出：按照指定框架提供分析结果
5. 具体化建议：提供具体、可操作的解决方案和建议

请确保分析结果具有专业性、针对性和实用性。"""
        
        headers = {
            'Authorization': f'Bearer {Config.DASHSCOPE_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': Config.DASHSCOPE_MODEL or 'qwen-max',
            'input': {
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt}
                ]
            },
            'parameters': {
                'temperature': Config.AI_TEMPERATURE or 0.7,
                'top_p': Config.AI_TOP_P or 0.8
            }
        }
        
        response = requests.post(
            Config.DASHSCOPE_API_BASE or 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('output', {}).get('text', '')
            return {'analysis': analysis}
        else:
            print(f"\u901a\u4e49\u5343\u95eeAPI\u8c03\u7528\u5931\u8d25: {response.status_code}, {response.text}")
            return _simulate_ai_analysis(title, description, equipment_type, phase)
    
    except ImportError:
        print("requests\u5e93\u672a\u5b89\u88c5\uff0c\u4f7f\u7528\u6a21\u62df\u5206\u6790")
        return _simulate_ai_analysis(title, description, equipment_type, phase)
    except Exception as e:
        print(f"\u901a\u4e49\u5343\u95ee\u5206\u6790\u5931\u8d25: {str(e)}")
        return _simulate_ai_analysis(title, description, equipment_type, phase)


def _simulate_ai_analysis(title, description, equipment_type=None, phase=None):
    """模拟AI分析（当没有配置AI服务时使用）"""
    # 改进的模拟分析，避免千篇一律
    import random
    
    # 根据问题内容和设备类型生成更具针对性的分析
    problem_keywords = ['设计', '制造', '材料', '工艺', '使用', '维护', '环境', '兼容']
    solution_keywords = ['优化', '改进', '更换', '培训', '规范', '防护', '更新', '升级']
    
    # 基于设备类型和问题描述选择可能的原因
    equipment_type_lower = (equipment_type or "").lower()
    description_lower = (description or "").lower()
    
    # 内部原因分析
    internal_causes = []
    if '设计' in description_lower or '参数' in description_lower or equipment_type_lower in ['机械', '电子', '软件']:
        internal_causes.append("- 设计层面：设计参数可能不符合实际使用需求，设计验证环节存在不足")
    elif '制造' in description_lower or '生产' in description_lower or '工艺' in description_lower:
        internal_causes.append("- 制造层面：制造工艺参数可能未严格按照设计要求执行")
    elif '材料' in description_lower or '材质' in description_lower:
        internal_causes.append("- 材料层面：所选材料可能不符合设备运行要求")
    else:
        internal_causes.append(f"- 设计层面：{random.choice(['设计参数', '设计标准', '设计验证'])}可能存在不足")
    
    internal_causes.append("- 制造层面：制造工艺参数可能未严格按照设计要求执行")
    internal_causes.append("- 维护层面：维护流程可能未覆盖该类型问题的预防")
    
    # 外部原因分析
    external_causes = []
    if '环境' in description_lower or '温度' in description_lower or '湿度' in description_lower:
        external_causes.append("- 环境因素：设备运行环境可能超出设计预期（如温度、湿度、振动等）")
    elif '使用' in description_lower or '操作' in description_lower:
        external_causes.append("- 使用条件：实际操作方式或负载情况可能与设计预期不符")
    else:
        external_causes.append(f"- 环境因素：{random.choice(['温度', '湿度', '振动', '腐蚀'])}等环境因素可能影响设备运行")
    
    external_causes.append("- 使用条件：实际操作方式或负载情况可能与设计预期不符")
    external_causes.append("- 外部干扰：可能存在外部因素影响设备正常运行")
    
    # 问题分类
    categories = ['设计缺陷', '制造缺陷', '材料问题', '工艺问题', '使用不当', '维护不足', '环境因素', '兼容性问题']
    problem_category = random.choice(categories)
    
    # 严重程度
    severity_levels = ['低', '中', '高', '严重']
    severity = random.choice(severity_levels)
    
    equipment_context = f"设备类型: {equipment_type}" if equipment_type else "设备类型: 未指定"
    phase_context = f"发现阶段: {phase}" if phase else "发现阶段: 未指定"
    
    analysis = f"""AI分析结果:

问题分类: {problem_category}

系统内部原因分析: 
{chr(10).join(internal_causes)}

系统外部原因分析:
{chr(10).join(external_causes)}

解决方案: 
   1. 重新评估设计参数，确保符合实际使用需求
   2. 加强制造过程中的质量控制
   3. 优化维护流程，增加针对性检查项目
   4. 评估并改善设备运行环境

问题严重程度: {severity}

根本原因分析: 设计验证环节不足导致未充分考虑实际使用条件

{equipment_context}
{phase_context}
原始问题: {title} - {description}"""
    return {'analysis': analysis}


def extract_category_from_ai_response(ai_response, title, description):
    """
    从AI响应中提取分类信息
    
    Args:
        ai_response: AI分析响应
        title: 问题标题
        description: 问题描述
    
    Returns:
        dict: 包含分类信息的字典
    """
    try:
        # 尝试从AI响应中提取分类信息
        # 改进的分类提取，利用更详细的AI分析结果
        problem_category_id = 1  # 默认值
        solution_category_id = 1  # 默认值
        priority = 'medium'  # 默认优先级
        confidence = 0.7  # 默认置信度
        
        # 提取AI响应的各个部分进行分析
        # 使用更精确的模式匹配来提取问题分类
        import re
        
        # 从AI响应中提取问题分类部分
        problem_category_match = re.search(r'问题分类[:：]\s*([^\n\r]+)', ai_response)
        if problem_category_match:
            category_text = problem_category_match.group(1).strip()
            
            # 问题分类映射
            category_mapping = {
                '设计缺陷': 1,
                '制造缺陷': 2,
                '材料问题': 3,
                '工艺问题': 4,
                '使用不当': 5,
                '维护不足': 6,
                '环境因素': 7,
                '兼容性问题': 8
            }
            
            # 精确匹配
            for category_name, category_id in category_mapping.items():
                if category_name in category_text:
                    problem_category_id = category_id
                    break
        
        # 如果没有找到精确匹配，使用关键词匹配
        if problem_category_id == 1:  # 仍然是默认值
            ai_response_lower = ai_response.lower()
            
            # 问题分类映射 - 基于系统内部原因和外部原因分析
            # 内部原因相关关键词
            internal_design_keywords = ['设计', 'design', '设计参数', '设计验证', '设计假设', '设计缺陷', '设计标准']
            internal_production_keywords = ['制造', 'production', '制造缺陷', '生产工艺', '生产流程', '工艺参数']
            internal_material_keywords = ['材料', 'material', '材料规格', '材料问题', '材料选择']
            internal_process_keywords = ['工艺', 'process', '工艺问题', '工艺参数', '质量控制']
            internal_maintenance_keywords = ['维护', 'maintenance', '维护流程', '维护标准', '维护不足']
            
            # 外部原因相关关键词
            external_environment_keywords = ['环境', 'environment', '温度', '湿度', '振动', '腐蚀', '环境因素']
            external_usage_keywords = ['使用', 'use', '使用不当', '操作', '负载', '操作条件', '使用条件']
            external_compatibility_keywords = ['兼容', 'compatibility', '兼容性', '外部干扰', '电磁干扰']
            
            # 计算各部分关键词匹配数量以确定主要分类
            internal_design_matches = sum(1 for keyword in internal_design_keywords if keyword in ai_response_lower)
            internal_production_matches = sum(1 for keyword in internal_production_keywords if keyword in ai_response_lower)
            internal_material_matches = sum(1 for keyword in internal_material_keywords if keyword in ai_response_lower)
            internal_process_matches = sum(1 for keyword in internal_process_keywords if keyword in ai_response_lower)
            internal_maintenance_matches = sum(1 for keyword in internal_maintenance_keywords if keyword in ai_response_lower)
            external_environment_matches = sum(1 for keyword in external_environment_keywords if keyword in ai_response_lower)
            external_usage_matches = sum(1 for keyword in external_usage_keywords if keyword in ai_response_lower)
            external_compatibility_matches = sum(1 for keyword in external_compatibility_keywords if keyword in ai_response_lower)
            
            # 选择匹配度最高的分类
            category_scores = {
                1: internal_design_matches,  # 设计缺陷
                2: internal_production_matches,  # 制造缺陷
                3: internal_material_matches,  # 材料问题
                4: internal_process_matches,  # 工艺问题
                5: external_usage_matches,  # 使用不当
                6: internal_maintenance_matches,  # 维护不足
                7: external_environment_matches,  # 环境因素
                8: external_compatibility_matches  # 兼容性问题
            }
            
            # 找到最高分的分类
            problem_category_id = max(category_scores, key=category_scores.get)
            if category_scores[problem_category_id] == 0:  # 如果没有匹配，使用默认关键词匹配
                if any(keyword in ai_response_lower for keyword in ['设计', 'design', '设计缺陷']):
                    problem_category_id = 1
                elif any(keyword in ai_response_lower for keyword in ['制造', 'production', '制造缺陷']):
                    problem_category_id = 2
                elif any(keyword in ai_response_lower for keyword in ['材料', 'material', '材料问题']):
                    problem_category_id = 3
                elif any(keyword in ai_response_lower for keyword in ['工艺', 'process', '工艺问题']):
                    problem_category_id = 4
                elif any(keyword in ai_response_lower for keyword in ['使用', 'use', '使用不当']):
                    problem_category_id = 5
                elif any(keyword in ai_response_lower for keyword in ['维护', 'maintenance', '维护不足']):
                    problem_category_id = 6
                elif any(keyword in ai_response_lower for keyword in ['环境', 'environment', '环境因素']):
                    problem_category_id = 7
                elif any(keyword in ai_response_lower for keyword in ['兼容', 'compatibility', '兼容性']):
                    problem_category_id = 8
        
        # 解决方案分类映射 - 使用更精确的匹配
        solution_category_match = re.search(r'解决方案[:：]\s*[^\n\r]*', ai_response)
        if solution_category_match:
            solution_text = solution_category_match.group(0).lower()
            
            solution_category_mapping = {
                1: ['设计优化', 'design optimization', '重新设计', '设计参数', '设计验证'],
                2: ['工艺改进', 'process improvement', '生产工艺', '流程优化'],
                3: ['材料更换', 'material replacement', '材料升级', '材料选择'],
                4: ['培训', 'training', '使用培训', '操作培训'],
                5: ['维护规范', 'maintenance standard', '维护流程', '保养规范'],
                6: ['防护', 'protection', '防护措施', '环境适应'],
                7: ['软件', 'software', '更新', '软件升级'],
                8: ['硬件', 'hardware', '升级', '硬件更换']
            }
            
            solution_scores = {}
            for category_id, keywords in solution_category_mapping.items():
                score = sum(1 for keyword in keywords if keyword in solution_text)
                solution_scores[category_id] = score
            
            solution_category_id = max(solution_scores, key=solution_scores.get) if solution_scores else 1
        else:
            # 如果没有找到解决方案标题，使用关键词匹配
            ai_response_lower = ai_response.lower()
            
            solution_design_matches = sum(1 for keyword in ['设计优化', 'design optimization', '重新设计', '设计参数', '设计验证'] if keyword in ai_response_lower)
            solution_process_matches = sum(1 for keyword in ['工艺改进', 'process improvement', '生产工艺', '流程优化'] if keyword in ai_response_lower)
            solution_material_matches = sum(1 for keyword in ['材料更换', 'material replacement', '材料升级', '材料选择'] if keyword in ai_response_lower)
            solution_training_matches = sum(1 for keyword in ['培训', 'training', '使用培训', '操作培训'] if keyword in ai_response_lower)
            solution_maintenance_matches = sum(1 for keyword in ['维护规范', 'maintenance standard', '维护流程', '保养规范'] if keyword in ai_response_lower)
            solution_protection_matches = sum(1 for keyword in ['防护', 'protection', '防护措施', '环境适应'] if keyword in ai_response_lower)
            solution_software_matches = sum(1 for keyword in ['软件', 'software', '更新', '软件升级'] if keyword in ai_response_lower)
            solution_hardware_matches = sum(1 for keyword in ['硬件', 'hardware', '升级', '硬件更换'] if keyword in ai_response_lower)
            
            # 选择匹配度最高的解决方案分类
            solution_scores = {
                1: solution_design_matches,  # 设计优化
                2: solution_process_matches,  # 工艺改进
                3: solution_material_matches,  # 材料更换
                4: solution_training_matches,  # 使用培训
                5: solution_maintenance_matches,  # 维护规范
                6: solution_protection_matches,  # 防护措施
                7: solution_software_matches,  # 软件更新
                8: solution_hardware_matches   # 硬件升级
            }
            
            solution_category_id = max(solution_scores, key=solution_scores.get)
            if solution_scores[solution_category_id] == 0:  # 如果没有匹配，使用默认关键词匹配
                if any(keyword in ai_response_lower for keyword in ['设计优化', 'design optimization', '重新设计']):
                    solution_category_id = 1
                elif any(keyword in ai_response_lower for keyword in ['工艺改进', 'process improvement']):
                    solution_category_id = 2
                elif any(keyword in ai_response_lower for keyword in ['材料更换', 'material replacement']):
                    solution_category_id = 3
                elif any(keyword in ai_response_lower for keyword in ['培训', 'training', '使用培训']):
                    solution_category_id = 4
                elif any(keyword in ai_response_lower for keyword in ['维护规范', 'maintenance standard']):
                    solution_category_id = 5
                elif any(keyword in ai_response_lower for keyword in ['防护', 'protection', '防护措施']):
                    solution_category_id = 6
                elif any(keyword in ai_response_lower for keyword in ['软件', 'software', '更新']):
                    solution_category_id = 7
                elif any(keyword in ai_response_lower for keyword in ['硬件', 'hardware', '升级']):
                    solution_category_id = 8
        
        # 优先级映射 - 改进的优先级提取，使用正则表达式精确匹配
        priority_patterns = [
            (r'问题严重程度[:：]\s*(严重|critical|危急|紧急|重大|致命)', 'critical'),
            (r'问题严重程度[:：]\s*(高|high|重要|关键|主要)', 'high'),
            (r'问题严重程度[:：]\s*(中|medium|一般|普通)', 'medium'),
            (r'问题严重程度[:：]\s*(低|low|轻微|较小|不重要)', 'low')
        ]
        
        for pattern, priority_level in priority_patterns:
            match = re.search(pattern, ai_response)
            if match:
                priority = priority_level
                break
        else:
            # 如果没有找到问题严重程度标题，使用通用关键词
            ai_response_lower = ai_response.lower()
            priority_keywords = {
                'critical': ['严重', 'critical', '危急', '紧急', '重大', '致命'],
                'high': ['高', 'high', '重要', '关键', '主要'],
                'medium': ['中', 'medium', '一般', '普通'],
                'low': ['低', 'low', '轻微', '较小', '不重要']
            }
            
            for priority_level, keywords in priority_keywords.items():
                if any(keyword in ai_response_lower for keyword in keywords):
                    priority = priority_level
                    break
        
        # 提取置信度（如果有）
        confidence_matches = re.findall(r'置信度[:：]\s*([\d.]+)', ai_response)
        if confidence_matches:
            try:
                confidence = float(confidence_matches[0])
                confidence = max(0.0, min(1.0, confidence))  # 限制在0-1之间
            except ValueError:
                pass
        
        return {
            'problem_category_id': problem_category_id,
            'solution_category_id': solution_category_id,
            'priority': priority,
            'confidence': confidence
        }
    
    except Exception as e:
        print(f'从AI响应中提取分类信息失败: {str(e)}')
        # 返回默认值
        return {
            'problem_category_id': 1,
            'solution_category_id': 1,
            'priority': 'medium',
            'confidence': 0.7
        }


def get_similar_problems_by_vector(query_text, top_k=5, min_similarity=0.1):
    """
    使用向量数据库查找相似问题
    
    Args:
        query_text: 查询文本
        top_k: 返回最相似的前k个问题
        min_similarity: 最小相似度阈值
    
    Returns:
        List[Dict]: 相似问题列表
    """
    try:
        vector_db = get_vector_db()
        results = vector_db.search_similar_problems(query_text, n_results=top_k, min_similarity=min_similarity)
        return results
    except Exception as e:
        print(f'向量数据库搜索相似问题失败: {str(e)}')
        return []


def get_design_suggestions_for_query(query_text, historical_problems):
    """
    根据查询获取设计建议
    
    Args:
        query_text: 用户查询文本
        historical_problems: 历史问题列表
    
    Returns:
        str: AI生成的设计建议
    """
    try:
        # 首先使用向量数据库查找相似问题
        vector_similar_problems = get_similar_problems_by_vector(query_text, top_k=10)
        
        # 构建历史问题文本
        problems_text = ""
        # 先添加向量数据库中找到的相似问题
        for p in vector_similar_problems:
            metadata = p.get('metadata', {})
            problems_text += f"""
相似问题: {metadata.get('title', '未知标题')}
描述: {metadata.get('description', '无描述')}
AI分析: {metadata.get('ai_analysis', '无分析')}
解决方案: {metadata.get('solution_description', '无解决方案')}
发现阶段: {metadata.get('phase', '未知阶段')}
"""
        
        # 如果向量搜索结果不够，补充数据库中的其他问题
        if len(vector_similar_problems) < 5:
            for p in historical_problems:
                problems_text += f"""
问题: {p.title}
描述: {p.description}
AI分析: {p.ai_analysis or '未分析'}
解决方案: {p.solution_description or '无'}
发现阶段: {p.phase}
"""

        prompt = f"""您是一个专业的设备设计顾问，帮助工程师在设计阶段规避潜在问题。基于以下历史问题数据库，请分析用户的设计查询。

历史问题数据：
{problems_text}

用户查询: \"{query_text}\"

请提供以下内容：
1. 是否存在类似的历史问题
2. 如果存在，这些问题的根本原因是什么
3. 如何在当前设计中避免这些问题
4. 具体的设计建议和最佳实践
5. 需要特别注意的关键点

请提供详细、专业的建议，帮助用户在设计阶段规避潜在问题。"""
        
        if Config.AI_PROVIDER == 'openai':
            return _query_with_openai(prompt)
        elif Config.AI_PROVIDER == 'dashscope':
            import requests
            from config import Config
            
            headers = {
                'Authorization': f'Bearer {Config.DASHSCOPE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': Config.DASHSCOPE_MODEL or 'qwen-max',
                'input': {
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的设备设计顾问，帮助工程师在设计阶段规避潜在问题。'},
                        {'role': 'user', 'content': prompt}
                    ]
                },
                'parameters': {
                    'temperature': 0.4,  # 稍微降低温度以获得更准确的技术建议
                }
            }
            
            response = requests.post(
                Config.DASHSCOPE_API_BASE or 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('output', {}).get('text', '')
            else:
                print(f"通义千问API调用失败: {response.status_code}, {response.text}")
                return f"基于历史数据分析，针对您的查询 '{query_text}'，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"
        else:
            # 模拟响应
            return f"基于历史数据分析，针对您的查询 '{query_text}'，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"
    
    except Exception as e:
        print(f'AI查询失败: {str(e)}')
        return f"针对您的查询 '{query_text}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性"


def _query_with_openai(prompt):
    """使用OpenAI API进行查询"""
    try:
        import openai
        from config import Config
        
        openai.api_key = Config.OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL or "gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4  # 降低温度以获得更准确的技术建议
        )
        
        analysis = response.choices[0].message['content']
        return analysis
    
    except ImportError:
        print("OpenAI库未安装，返回模拟响应")
        return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"
    except Exception as e:
        print(f"OpenAI查询失败: {str(e)}")
        return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"


def generate_internal_solution_focus(problem_title, problem_description, ai_analysis_result, equipment_type=None, phase=None):
    """
    生成着重解决内部原因引发故障的解决方案
    
    Args:
        problem_title: 问题标题
        problem_description: 问题描述
        ai_analysis_result: AI分析结果
        equipment_type: 设备类型（可选）
        phase: 发现阶段（可选）
    
    Returns:
        str: 针对内部原因的解决方案
    """
    try:
        equipment_context = f"设备类型: {equipment_type}" if equipment_type else ""
        phase_context = f"发现阶段: {phase}" if phase else ""
        
        context_info = ""
        if equipment_context or phase_context:
            context_info = f"上下文信息:\n{equipment_context}\n{phase_context}\n\n"
        
        prompt = f"""基于以下设备问题和AI分析结果，请专门针对系统内部原因生成详细的解决方案：

{context_info}问题标题: {problem_title}
问题描述: {problem_description}
AI分析结果: {ai_analysis_result}

请重点关注以下方面生成解决方案：
1. 设计层面的改进措施（结合设备特点和发现问题的阶段）
2. 制造工艺的优化方案（考虑具体工艺参数和质量控制）
3. 材料选择的改进建议（根据设备使用要求和环境）
4. 内部流程和规范的完善（基于发现问题的阶段）
5. 质量控制和测试环节的加强（针对性改进）
6. 维护保养流程的优化（预防类似问题再次发生）

请提供具体、可执行、有针对性的内部改进方案，以减少由于系统内部原因导致的故障。"""
        
        # 根据配置使用不同的AI服务
        if Config.AI_PROVIDER == 'openai':
            import openai
            from config import Config
            
            openai.api_key = Config.OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的设备工程专家，专注于解决系统内部原因导致的故障。请结合设备类型和发现阶段提供详细、具体的内部改进方案。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=Config.AI_TEMPERATURE or 0.3
            )
            
            solution = response.choices[0].message['content']
            return solution
        elif Config.AI_PROVIDER == 'dashscope':  # 通义千问
            import requests
            
            headers = {
                'Authorization': f'Bearer {Config.DASHSCOPE_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': Config.DASHSCOPE_MODEL or 'qwen-max',
                'input': {
                    'messages': [
                        {'role': 'system', 'content': '你是一个专业的设备工程专家，专注于解决系统内部原因导致的故障。请结合设备类型和发现阶段提供详细、具体的内部改进方案。'},
                        {'role': 'user', 'content': prompt}
                    ]
                },
                'parameters': {
                    'temperature': Config.AI_TEMPERATURE or 0.7,
                    'top_p': Config.AI_TOP_P or 0.8
                }
            }
            
            response = requests.post(
                Config.DASHSCOPE_API_BASE or 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                solution = result.get('output', {}).get('text', '')
                return solution
            else:
                print(f"通义千问API调用失败: {response.status_code}, {response.text}")
                return _generate_internal_solution_simulation(problem_title, problem_description)
        else:
            # 模拟响应（如果没有配置AI服务）
            return _generate_internal_solution_simulation(problem_title, problem_description)
    
    except Exception as e:
        print(f'生成内部原因解决方案失败: {str(e)}')
        return _generate_internal_solution_simulation(problem_title, problem_description)


def _generate_internal_solution_simulation(problem_title, problem_description, equipment_type=None, phase=None):
    """模拟生成内部原因解决方案"""
    equipment_context = f"设备类型: {equipment_type}" if equipment_type else ""
    phase_context = f"发现阶段: {phase}" if phase else ""
    
    context_info = ""
    if equipment_context or phase_context:
        context_info = f"\n上下文信息:\n{equipment_context}\n{phase_context}\n"
    
    solution = f"""内部原因解决方案:{context_info}

1. 设计优化:
   - 重新评估设计参数，确保设计余量充足
   - 增加设计验证环节，包括仿真分析和原型测试
   - 考虑使用更可靠的组件和材料
   - 结合设备特点优化设计方案

2. 制造工艺改进:
   - 优化生产工艺流程，减少制造误差
   - 加强生产过程中的质量控制
   - 实施更严格的工艺标准和检验程序
   - 根据发现问题的阶段调整制造重点

3. 材料选择改进:
   - 评估当前材料的适用性
   - 考虑使用更高性能或更可靠的替代材料
   - 加强材料入库检验程序
   - 根据设备使用环境选择合适材料

4. 质量控制加强:
   - 增加出厂前的测试项目
   - 实施更全面的质量管理体系
   - 定期进行质量审核和改进
   - 针对性加强关键质量控制点

5. 维护保养优化:
   - 制定更详细的维护计划
   - 提供维护人员培训
   - 建立预防性维护体系
   - 根据设备特点和问题阶段优化维护策略

问题: {problem_title}
描述: {problem_description}"""
    return solution
