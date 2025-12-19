# 读取和更新 ai_analysis.py 文件中的错误
file_path = 'D:\\Users\\00596\\Desktop\\wenTiJi\\ai_analysis.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到有问题的行并修复
for i, line in enumerate(lines):
    if 'return f"针对您的查询' in line and '建议在设计时考虑以下几个方面：' in line:
        # 重建这一行，修复 f-string 语法
        lines[i] = "        return f\"针对您的查询 '" + query_text + "'，建议在设计时考虑以下几个方面：\n\n1. 材料选择的可靠性\n2. 环境适应性设计\n3. 维护便利性\"\n"
        break

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('已修复 f-string 语法错误')