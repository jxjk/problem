# 读取文件内容
with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复特定的 f-string 语法错误
# 将多行 f-string 修复为使用 \n 转义
content = content.replace(
    "return f\"针对您的查询 '{query_text}'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性\"",
    "return f\"针对您的查询 '{{query_text}}'，建议在设计时考虑以下几个方面：\\n\\n1. 材料选择的可靠性\\n2. 环境适应性设计\\n3. 维护便利性\"".replace('{query_text}', "' + query_text + '")
)

# 写回文件
with open('D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("已修复 f-string 语法错误")