#!/bin/bash
# 启动弹幕AI服务器

echo "======================================"
echo "抖音直播弹幕AI服务器启动脚本"
echo "======================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 检查依赖
echo "检查依赖..."
pip install -q -r requirements.txt

# 启动服务
echo "启动弹幕AI服务器..."
python danmaku_app.py
