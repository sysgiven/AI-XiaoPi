#!/usr/bin/env python3
"""
批量更新导入语句的脚本
将所有 'from config.' 改为 'from configs.'
"""

import os
import re

def update_imports_in_file(filepath):
    """更新单个文件中的导入语句"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 保存原始内容用于比较
        original_content = content

        # 替换 from config. 为 from configs.
        content = re.sub(r'from config\.', 'from configs.', content)

        # 如果内容有变化，写回文件
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"处理文件 {filepath} 时出错: {e}")
        return False

def main():
    """主函数"""
    # 需要更新的目录
    directories = ['core', 'plugins', 'configs']

    updated_count = 0
    total_files = 0

    for directory in directories:
        if not os.path.exists(directory):
            print(f"目录不存在: {directory}")
            continue

        # 遍历目录下的所有 Python 文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    total_files += 1
                    if update_imports_in_file(filepath):
                        updated_count += 1
                        print(f"已更新: {filepath}")

    print(f"\n处理完成！")
    print(f"总共检查文件: {total_files}")
    print(f"更新的文件: {updated_count}")

if __name__ == '__main__':
    main()
