import re

# 读取文件内容
file_path = 'D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找包含问题的代码段并修复
# 首先找到通义千问API失败时的返回值部分
pattern = r"return f\"基于历史数据分析，针对您的查询 '([^']*)'，我们发现了以下设计建议：\n*1\. 在设计阶段应特别注意材料选择\n*2\. 建议增加冗余设计提高可靠性\n*3\. 考虑环境因素对设备的影响\""

# 修复方法：将换行替换为 \n 转义字符
def replace_multiline_fstring(match):
    query_text = match.group(1)
    fixed = f"return f\"基于历史数据分析，针对您的查询 '{query_text}'，我们发现了以下设计建议：\\n\\n1. 在设计阶段应特别注意材料选择\\n2. 建议增加冗余设计提高可靠性\\n3. 考虑环境因素对设备的影响\""
    return fixed

# 应用修复
content = re.sub(pattern, replace_multiline_fstring, content, flags=re.MULTILINE)

# 查找另一个可能的问题位置（在模拟响应部分）
pattern2 = r"return f\"基于历史数据分析，针对您的查询 '([^']*)'，我们发现了以下设计建议：\s+1\. 在设计阶段应特别注意材料选择\s+2\. 建议增加冗余设计提高可靠性\s+3\. 考虑环境因素对设备的影响\""
content = re.sub(pattern2, replace_multiline_fstring, content, flags=re.MULTILINE)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("已修复 f-string 语法错误")