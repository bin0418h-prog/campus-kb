@echo off
chcp 65001 >nul
title CampusKB 校园知识库
cd /d %~dp0

echo [1/3] 启动数据库容器（需先打开 Docker Desktop）...
docker compose up -d

echo [2/3] 等待数据库就绪（首次启动约 20-40 秒）...
:wait_db
docker exec campus-kb-mysql-1 mysql -uroot -proot -e "SELECT 1" campuskb >nul 2>&1
if errorlevel 1 goto :retry
docker exec campus-kb-postgres-1 pg_isready -U postgres -q >nul 2>&1
if errorlevel 1 goto :retry
goto :ready
:retry
timeout /t 3 /nobreak >nul
goto :wait_db

:ready
echo [3/3] 启动服务并打开浏览器...
start http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
