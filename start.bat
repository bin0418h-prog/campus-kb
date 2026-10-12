@echo off
chcp 65001 >nul
title CampusKB 校园知识库
cd /d %~dp0

echo [1/3] 启动数据库容器（需先打开 Docker Desktop）...
docker compose up -d

echo [2/3] 等待数据库就绪...
timeout /t 10 /nobreak >nul

echo [3/3] 启动服务并打开浏览器...
start http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
