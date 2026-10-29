# 服务器部署说明

目标：把 campus-kb 部署到一台公网 Linux 服务器，任何人可通过 `http://服务器IP:8000` 访问。

## 服务器要求

- Ubuntu 22.04 / 24.04，2核2G 起（内存紧则加 2G swap）
- 防火墙（安全组）放行 22、8000 端口

## 首次部署

```bash
# 1. 安装 Docker（阿里云镜像源）
curl -fsSL https://get.docker.com | sh

# 2. 拉代码（或直接 scp 上传项目目录）
git clone https://github.com/bin0418h-prog/campus-kb.git
cd campus-kb

# 3. 配置密钥（.env 不提交仓库，需手动创建）
cp .env.example .env
vim .env   # 填入 DEEPSEEK_API_KEY / EMBEDDING_API_KEY / ADMIN_PASSWORD

# 4. 构建并启动
docker compose -f docker-compose.prod.yml up -d --build

# 5. 验证
curl http://127.0.0.1:8000/health
docker compose -f docker-compose.prod.yml ps
```

## 日常运维

```bash
docker compose -f docker-compose.prod.yml logs -f app   # 看应用日志
docker compose -f docker-compose.prod.yml restart app   # 重启应用
docker stats                                            # 看容器资源占用
free -h                                                 # 看内存
ss -tlnp                                                # 看端口监听
```

## 常见问题

| 现象 | 排查 |
| --- | --- |
| 公网访问不了 | 安全组/防火墙是否放行 8000；`ss -tlnp` 看是否监听 0.0.0.0 |
| 启动后立刻退出 | `docker compose logs app`，多半是数据库没就绪或 .env 缺 key |
| 内存不足被 OOM | `dmesg \| grep -i oom`，加 swap 或减少 MySQL 缓冲池 |
| 重新上传文档后检索不到 | 确认返回 chunks 数 > 0，再刷新页面 |

## 面试可讲

- 为什么数据库端口不映射到宿主机：公网暴露 5432/3306 会被扫库
- 为什么 app 用 depends_on + healthcheck：数据库初始化需要几十秒
- 2核2G 上跑三个容器的取舍：MySQL 缓冲池调小、加 swap
