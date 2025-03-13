@echo off
echo 正在启动Minecraft AI...

REM 启动机器人服务器
start cmd /k "cd bot && npm install && npm start"

REM 等待几秒让服务器启动
timeout /t 5

REM 启动Python程序
python run.py --local --cache --prediction

pause 