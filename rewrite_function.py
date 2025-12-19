#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to rewrite the entire _query_with_openai function with correct syntax
"""

def fix_query_with_openai_function():
    """Rewrite the _query_with_openai function with proper escaped strings"""
    
    # Read the entire file
    with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Define the corrected function
    fixed_function = '''def _query_with_openai(prompt: str) -> str:
    """使用OpenAI API进行查询"""
    try:
        import openai
        from config import Config
        
        openai.api_key = Config.OPENAI_API_KEY
        
        response = openai.ChatCompletion.create(
            model=Config.OPENAI_MODEL or "gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的设备设计顾问，帮助工程师在设计阶段规避潜在问题。请严格按照结构化格式返回分析结果。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,  # 降低温度以获得更准确的技术建议
            response_format={"type": "json_object"}  # 请求JSON格式响应
        )
        
        analysis = response.choices[0].message['content']
        return analysis
    
    except ImportError:
        print("OpenAI库未安装，返回模拟响应")
        return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"
    except Exception as e:
        print(f"OpenAI查询失败: {str(e)}")
        return "基于历史数据分析，针对您的查询，我们发现了以下设计建议：\n\n1. 在设计阶段应特别注意材料选择\n2. 建议增加冗余设计提高可靠性\n3. 考虑环境因素对设备的影响"'''

    # Find the original function
    start_pos = content.find('def _query_with_openai(prompt: str) -> str:')
    if start_pos == -1:
        print("Could not find the function definition")
        return
    
    # Find the end of the function by looking for the next function definition or class
    # Look for the next 'def ' after some distance to make sure we get the full function
    remaining_content = content[start_pos:]
    
    # Find end by looking for the first line that has no indentation after a block of indented lines
    lines = remaining_content.split('\n')
    
    # Find end by looking for the next def or end of file
    # The function ends when we have a line that's not indented or a new def
    end_pos = start_pos
    in_function = False
    for i, line in enumerate(lines[1:], 1):  # Skip the def line
        if line.strip() == "":  # Empty line, continue
            continue
        # Check indentation level
        stripped = line.lstrip()
        if stripped.startswith('def ') or stripped.startswith('class '):
            # Found the next function or class, this is our end
            end_pos = start_pos + len('\n'.join(lines[:i]))
            break
        elif stripped and len(line) - len(stripped) == 0:  # No indentation (not counting empty lines)
            # This line is not indented, could be end of function
            # But we should ensure we're not just at an empty line inside the function
            # Look ahead a few lines to see if we're really at the end
            j = i
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                next_nonempty = lines[j]
                if len(next_nonempty) - len(next_nonempty.lstrip()) == 0 and (next_nonempty.startswith('def ') or next_nonempty.startswith('class ')):
                    end_pos = start_pos + len('\n'.join(lines[:i]))
                    break
    
    # If we couldn't find an explicit end, try a different approach
    # Look for the next function definition after this one
    next_def_pos = content.find('\ndef ', start_pos + 1)
    if next_def_pos != -1:
        # Extract the part that likely contains the whole function
        potential_function = content[start_pos:next_def_pos]
        
        # Replace the original function with the fixed one
        new_content = content[:start_pos] + fixed_function + content[next_def_pos:]
        
        # Write the fixed content back to the file
        with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print('Function has been replaced with corrected version.')
    else:
        print("Could not determine function end clearly")


if __name__ == "__main__":
    fix_query_with_openai_function()