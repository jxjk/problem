
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
def analyze_problem_with_ai(title, description):
    """
    使用AI分析问题
    
    Args:
        title: 问题标题
        description: 问题描述
    
    Returns:
        dict: 包含AI分析结果的字典
    """
    try:
        # 构建AI提示
        prompt = f"""请对以下设备问题进行详细分析，将问题原因分为系统内部原因和系统外部原因两部分：

问题标题: {title}
问题描述: {description}

请提供以下信息：
1. 问题分类（从以下选项中选择：设计缺陷、制造缺陷、材料问题、工艺问题、使用不当、维护不足、环境因素、兼容性问题）
2. 系统内部原因分析（与设计、制造、材料、工艺、维护等内部因素相关）
3. 系统外部原因分析（与环境、使用条件、外部干扰等外部因素相关）
4. 建议的解决方案（优先考虑内部原因的解决方案）
5. 问题严重程度（低、中、高、严重）
6. 在哪个阶段发现（设计、开发、使用、维护）

请以结构化文本格式返回分析结果，重点突出内部原因的解决方案。"""
        
        # 根据配置使用不同的AI服务
        if Config.AI_PROVIDER == 'openai':
            return _analyze_with_openai(prompt)
        elif Config.AI_PROVIDER == 'dashscope':  # 通义千问
            return _analyze_with_dashscope(prompt, title, description)
        else:
            # 模拟AI响应（如果没有配置AI服务）
            return _simulate_ai_analysis(title, description)
    
    except Exception as e:
        print(f'AI分析失败: {str(e)}')
        # 返回模拟分析结果以确保系统正常运行
        return _simulate_ai_analysis(title, description)


def _analyze_with_openai(prompt):
    """使用OpenAI API进行分析"""
    try:
        import openai
        from config import Config
        
        openai.api_key = Config.OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的设备问题分析专家，帮助工程师分析设备问题并提供解决方案。请将问题原因分为系统内部原因和系统外部原因两部分进行分析，并着重提出解决内部原因的方案。"},
                {"role": "user", "content": prompt}
            ],
            temperature=Config.AI_TEMPERATURE or 0.3
        )
        
        analysis = response.choices[0].message['content']
        return {'analysis': analysis}
    
    except ImportError:
        print("OpenAI\u5e93未安装，使用模拟分析")
        return _simulate_ai_analysis("\u95ee\u9898", "\u95ee\u9898\u63cf\u8ff0")
    except Exception as e:
        print(f"OpenAI\u5206\u6790\u5931\u8d25: {str(e)}")
        return _simulate_ai_analysis("\u95ee\u9898", "\u95ee\u9898\u63cf\u8ff0")


def _analyze_with_dashscope(prompt, title, description):
    """使用通义千问API进行分析"""
    try:
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
                    {'role': 'system', 'content': '你是一个专业的设备问题分析专家，帮助工程师分析设备问题并提供解决方案。请将问题原因分为系统内部原因和系统外部原因两部分进行分析，并着重提出解决内部原因的方案。'},
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
            return _simulate_ai_analysis(title, description)
    
    except ImportError:
        print("requests\u5e93\u672a\u5b89\u88c5\uff0c\u4f7f\u7528\u6a21\u62df\u5206\u6790")
        return _simulate_ai_analysis(title, description)
    except Exception as e:
        print(f"\u901a\u4e49\u5343\u95ee\u5206\u6790\u5931\u8d25: {str(e)}")
        return _simulate_ai_analysis(title, description)


def _simulate_ai_analysis(title, description):
    """模拟AI分析（当没有配置AI服务时使用）"""
    # 这里可以使用一些基本的规则来模拟AI分析
    analysis = f"""AI分析结果:\n    \n问题分类: 设计缺陷\n系统内部原因分析: 根据问题描述，可能是由于设计阶段考虑不周、设计参数不当或设计验证不充分导致的问题\n系统外部原因分析: 可能与使用环境超出设计预期、操作条件变化或外部干扰因素有关\n解决方案: 建议重新评估设计方案，增加设计验证环节，优化内部设计参数以提高对外部环境变化的适应性\n问题严重程度: 中等\n发现阶段: 设计    \n\n原始问题: {title} - {description}\n    """
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
        # 这里我们使用简单的关键词匹配来模拟分类提取
        problem_category_id = 1  # 默认值
        solution_category_id = 1  # 默认值
        priority = 'medium'  # 默认优先级
        confidence = 0.7  # 默认置信度
        
        # 基于AI响应内容的简单分类
        response_lower = ai_response.lower()
        
        # 问题分类映射
        if any(keyword in response_lower for keyword in ['设计', 'design', '设计缺陷']):
            problem_category_id = 1
        elif any(keyword in response_lower for keyword in ['制造', 'production', '制造缺陷']):
            problem_category_id = 2
        elif any(keyword in response_lower for keyword in ['材料', 'material', '材料问题']):
            problem_category_id = 3
        elif any(keyword in response_lower for keyword in ['工艺', 'process', '工艺问题']):
            problem_category_id = 4
        elif any(keyword in response_lower for keyword in ['使用', 'use', '使用不当']):
            problem_category_id = 5
        elif any(keyword in response_lower for keyword in ['维护', 'maintenance', '维护不足']):
            problem_category_id = 6
        elif any(keyword in response_lower for keyword in ['环境', 'environment', '环境因素']):
            problem_category_id = 7
        elif any(keyword in response_lower for keyword in ['兼容', 'compatibility', '兼容性']):
            problem_category_id = 8
        
        # 解决方案分类映射
        if any(keyword in response_lower for keyword in ['设计优化', 'design optimization', '重新设计']):
            solution_category_id = 1
        elif any(keyword in response_lower for keyword in ['工艺改进', 'process improvement']):
            solution_category_id = 2
        elif any(keyword in response_lower for keyword in ['材料更换', 'material replacement']):
            solution_category_id = 3
        elif any(keyword in response_lower for keyword in ['培训', 'training', '使用培训']):
            solution_category_id = 4
        elif any(keyword in response_lower for keyword in ['维护规范', 'maintenance standard']):
            solution_category_id = 5
        elif any(keyword in response_lower for keyword in ['防护', 'protection', '防护措施']):
            solution_category_id = 6
        elif any(keyword in response_lower for keyword in ['软件', 'software', '更新']):
            solution_category_id = 7
        elif any(keyword in response_lower for keyword in ['硬件', 'hardware', '升级']):
            solution_category_id = 8
        
        # 优先级映射
        if any(keyword in response_lower for keyword in ['严重', 'critical', '危急']):
            priority = 'critical'
        elif any(keyword in response_lower for keyword in ['高', 'high', '重要']):
            priority = 'high'
        elif any(keyword in response_lower for keyword in ['低', 'low', '轻微']):
            priority = 'low'
        
        # 提取置信度（如果有）
        confidence_matches = re.findall(r'置信度[:：]\s*([\d.]+)', ai_response)
        if confidence_matches:
            try:
                confidence = float(confidence_matches[0])
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


def generate_internal_solution_focus(problem_title, problem_description, ai_analysis_result):
    """
    生成着重解决内部原因引发故障的解决方案
    
    Args:
        problem_title: 问题标题
        problem_description: 问题描述
        ai_analysis_result: AI分析结果
    
    Returns:
        str: 针对内部原因的解决方案
    """
    try:
        prompt = f"""基于以下设备问题和AI分析结果，请专门针对系统内部原因生成详细的解决方案：

问题标题: {problem_title}
问题描述: {problem_description}
AI分析结果: {ai_analysis_result}

请重点关注以下方面生成解决方案：
1. 设计层面的改进措施
2. 制造工艺的优化方案
3. 材料选择的改进建议
4. 内部流程和规范的完善
5. 质量控制和测试环节的加强
6. 维护保养流程的优化

请提供具体、可执行的内部改进方案，以减少由于系统内部原因导致的故障。"""
        
        # 根据配置使用不同的AI服务
        if Config.AI_PROVIDER == 'openai':
            import openai
            from config import Config
            
            openai.api_key = Config.OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model=Config.OPENAI_MODEL or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的设备工程专家，专注于解决系统内部原因导致的故障。请提供详细、具体的内部改进方案。"},
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
                        {'role': 'system', 'content': '你是一个专业的设备工程专家，专注于解决系统内部原因导致的故障。请提供详细、具体的内部改进方案。'},
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


def _generate_internal_solution_simulation(problem_title, problem_description):
    """模拟生成内部原因解决方案"""
    solution = f"""内部原因解决方案:

1. 设计优化:
   - 重新评估设计参数，确保设计余量充足
   - 增加设计验证环节，包括仿真分析和原型测试
   - 考虑使用更可靠的组件和材料

2. 制造工艺改进:
   - 优化生产工艺流程，减少制造误差
   - 加强生产过程中的质量控制
   - 实施更严格的工艺标准和检验程序

3. 材料选择改进:
   - 评估当前材料的适用性
   - 考虑使用更高性能或更可靠的替代材料
   - 加强材料入库检验程序

4. 质量控制加强:
   - 增加出厂前的测试项目
   - 实施更全面的质量管理体系
   - 定期进行质量审核和改进

5. 维护保养优化:
   - 制定更详细的维护计划
   - 提供维护人员培训
   - 建立预防性维护体系

问题: {problem_title}
描述: {problem_description}"""
    return solution
