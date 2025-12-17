@echo off
REM 启动弹幕AI服务器 - Windows版本

echo ======================================
echo 抖音直播弹幕AI服务器启动脚本
echo ======================================

REM 检查Python版本
python --version

REM 激活虚拟环境（如果存在）
if exist venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 检查依赖
echo 检查依赖...
pip install -q -r requirements.txt

REM 启动服务
echo 启动弹幕AI服务器...
python danmaku_app.py

pause
