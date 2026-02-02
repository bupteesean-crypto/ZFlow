# ZFlow Docker 部署（生产模式）

## 前置准备
- Docker + docker compose 已安装
- 项目根目录准备好 `.env`（可参考 `.env.example`）

## 启动
```bash
docker compose build
docker compose up -d
```

访问地址：
```
http://localhost:8080
```

## 初始化数据库（首次）
```bash
docker compose exec backend python -m app.db.init_db
```

## 常用操作
- 停止：
  ```bash
  docker compose down
  ```
- 重新构建并启动（代码有改动时）：
  ```bash
  docker compose down
  docker compose build
  docker compose up -d
  ```

## 端口与安全
- 只对外暴露前端端口：`8080`
- 后端与数据库仅在容器内网可访问

## 备注
- 前端通过 Nginx 反代 `/api` 到后端服务
- 前端默认请求 `/api/v1`，如需自定义可在 `frontend/.env` 设置 `VITE_API_BASE_URL`
- 如需更换端口，可修改 `docker-compose.yml` 的 `frontend.ports`
