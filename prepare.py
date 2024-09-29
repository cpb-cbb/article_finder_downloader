# 打开文件并读取内容
with open('input.csv', 'r', encoding='utf-8') as file:
    content = file.read()

# 替换逗号和换行符为空格
content = content.replace(',', ' ').replace('\n', ' ')

# 将右圆括号替换为换行符
content = content.replace(')', '\n')

# 将修改后的内容写回文件
with open('input.csv', 'w', encoding='utf-8') as file:
    file.write(content)

print("文件修改完成！")
