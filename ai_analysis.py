
"""
AI分析功能模块
处理问题的AI分析和分类
"""

import json
import re
from config import Config
import os

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
        prompt = f"""\u8bf7对以下设备问题进行分析：
        
问题标题: {title}
问题描述: {description}

请提供以下信息：
1. 问题分类（从以下选项中选择：设计缺陷、制造缺陷、材料问题、工艺问题、使用不当、维护不足、环境因素、兼容性问题）
2. 可能的原因分析
3. 建议的解决方案
4. 问题严重程度（低、中、高、严重）
5. 在哪个阶段发现（设计、开发、使用、维护）

请以结构化文本格式返回分析结果。"""
        
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
            messages=[{"role": "user", "content": prompt}],
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
                    {'role': 'system', 'content': '\u4f60\u662f\u4e00\u4e2a\u4e13\u4e1a\u7684\u8bbe\u5907\u95ee\u9898\u5206\u6790\u4e13\u5bb6\uff0c\u5e2e\u52a9\u5de5\u7a0b\u5e08\u5206\u6790\u8bbe\u5907\u95ee\u9898\u5e76\u63d0\u4f9b\u89e3\u51b3\u65b9\u6848\u3002'},
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
    analysis = f"""AI\u5206\u6790\u7ed3\u679c:\n    
\u95ee\u9898\u5206\u7c7b: \u8bbe\u8ba1\u7f3a\u9677
\u539f\u56e0\u5206\u6790: \u6839\u636e\u95ee\u9898\u63cf\u8ff0\uff0c\u53ef\u80fd\u662f\u7531\u4e8e\u8bbe\u8ba1\u9636\u6bb5\u8003\u8651\u4e0d\u5468\u5bfc\u81f4\u7684\u95ee\u9898
\u89e3\u51b3\u65b9\u6848: \u5efa\u8bae\u91cd\u65b0\u8bc4\u4f30\u8bbe\u8ba1\u65b9\u6848\uff0c\u589e\u52a0\u8bbe\u8ba1\u9a8c\u8bc1\u73af\u8282
\u4e25\u91cd\u7a0b\u5ea6: \u4e2d\u7b49
\u53d1\u73b0\u9636\u6bb5: \u8bbe\u8ba1    
\n\u539f\u59cb\u95ee\u9898: {title} - {description}
    """
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
        problems_text = ""
        for p in historical_problems:
            problems_text += f"""
问题: {p.title}
描述: {p.description}
AI分析: {p.ai_analysis or '\u672a\u5206\u6790'}
解\u51b3\u65b9\u6848: {p.solution_description or '\u65e0'}
发\u73b0\u9636\u6bb5: {p.phase}
"""

        prompt = f"""\u60a8\u662f\u4e00\u4e2a\u4e13\u4e1a\u7684\u8bbe\u5907\u8bbe\u8ba1\u987e\u95ee\uff0c\u5e2e\u52a9\u5de5\u7a0b\u5e08\u5728\u8bbe\u8ba1\u9636\u6bb5\u89c4\u907f\u6f5c\u5728\u95ee\u9898\u3002\u57fa\u4e8e\u4ee5\u4e0b\u5386\u53f2\u95ee\u9898\u6570\u636e\u5e93\uff0c\u8bf7\u5206\u6790\u7528\u6237\u7684\u8bbe\u8ba1\u67e5\u8be2\u3002

\u5386\u53f2\u95ee\u9898\u6570\u636e：
{problems_text}

\u7528\u6237\u67e5\u8be2: \"{query_text}\"

\u8bf7\u63d0\u4f9b\u4ee5\u4e0b\u5185\u5bb9：
1. \u662f\u5426\u5b58\u5728\u7c7b\u4f3c\u7684\u5386\u53f2\u95ee\u9898
2. \u5982\u679c\u5b58\u5728\uff0c\u8fd9\u4e9b\u95ee\u9898\u7684\u6839\u672c\u539f\u56e0\u662f\u4ec0\u4e48
3. \u5982\u4f55\u5728\u5f53\u524d\u8bbe\u8ba1\u4e2d\u907f\u514d\u8fd9\u4e9b\u95ee\u9898
4. \u5177\u4f53\u7684\u8bbe\u8ba1\u5efa\u8bae\u548c\u6700\u4f73\u5b9e\u8df5
5. \u9700\u8981\u7279\u522b\u6ce8\u610f\u7684\u5173\u952e\u70b9

\u8bf7\u63d0\u4f9b\u8be6\u7ec6\u3001\u4e13\u4e1a\u7684\u5efa\u8bae\uff0c\u5e2e\u52a9\u7528\u6237\u5728\u8bbe\u8ba1\u9636\u6bb5\u89c4\u907f\u6f5c\u5728\u95ee\u9898\u3002"""
        
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
                        {'role': 'system', 'content': '\u4f60\u662f\u4e00\u4e2a\u4e13\u4e1a\u7684\u8bbe\u5907\u8bbe\u8ba1\u987e\u95ee\uff0c\u5e2e\u52a9\u5de5\u7a0b\u5e08\u5728\u8bbe\u8ba1\u9636\u6bb5\u89c4\u907f\u6f5c\u5728\u95ee\u9898\u3002'},
                        {'role': 'user', 'content': prompt}
                    ]
                },
                'parameters': {
                    'temperature': 0.4,  # 稍微降低温度以获得更准\u786e\u7684\u6280\u672f\u5efa\u8bae
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
                print(f"\u901a\u4e49\u5343\u95eeAPI\u8c03\u7528\u5931\u8d25: {response.status_code}, {response.text}")
                return f"\u57fa\u4e8e\u5386\u53f2\u6570\u636e\u5206\u6790\uff0c\u9488\u5bf9\u60a8\u7684\u67e5\u8be2 '{query_text}'\uff0c\u6211\u4eec\u53d1\u73b0\u4e86\u4ee5\u4e0b\u8bbe\u8ba1\u5efa\u8bae\uff1a\n\n1. \u5728\u8bbe\u8ba1\u9636\u6bb5\u5e94\u7279\u522b\u6ce8\u610f\u6750\u6599\u9009\u62e9\n2. \u5efa\u8bae\u589e\u52a0\u5197\u4f59\u8bbe\u8ba1\u63d0\u9ad8\u53ef\u9760\u6027\n3. \u8003\u8651\u73af\u5883\u56e0\u7d20\u5bf9\u8bbe\u5907\u7684\u5f71\u54cd"
        else:
            # 模拟\u54cd应
            return f"\u57fa\u4e8e\u5386\u53f2\u6570\u636e\u5206\u6790\uff0c\u9488\u5bf9\u60a8\u7684\u67e5\u8be2 '{query_text}'\uff0c\u6211\u4eec\u53d1\u73b0\u4e86\u4ee5\u4e0b\u8bbe\u8ba1\u5efa\u8bae\uff1a\n\n1. \u5728\u8bbe\u8ba1\u9636\u6bb5\u5e94\u7279\u522b\u6ce8\u610f\u6750\u6599\u9009\u62e9\n2. \u5efa\u8bae\u589e\u52a0\u5197\u4f59\u8bbe\u8ba1\u63d0\u9ad8\u53ef\u9760\u6027\n3. \u8003\u8651\u73af\u5883\u56e0\u7d20\u5bf9\u8bbe\u5907\u7684\u5f71\u54cd"
    
    except Exception as e:
        print(f'AI\u67e5\u8be2\u5931\u8d25: {str(e)}')
        return f"\u9488\u5bf9\u60a8\u7684\u67e5\u8be2 '{query_text}'\uff0c\u5efa\u8bae\u5728\u8bbe\u8ba1\u65f6\u8003\u8651\u4ee5\u4e0b\u51e0\u4e2a\u65b9\u9762\uff1a\n\n1. \u6750\u6599\u9009\u62e9\u7684\u53ef\u9760\u6027\n2. \u73af\u5883\u9002\u5e94\u6027\u8bbe\u8ba1\n3. \u7ef4\u62a4\u4fbf\u5229\u6027"
