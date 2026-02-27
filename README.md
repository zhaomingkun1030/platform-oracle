# Platform Oracle

OpenShift 竞品分析智能体系统

## 项目简介

使用 LangChain Multi-Agent 架构开发的竞品分析系统，自动分析 Red Hat OpenShift CP 及 OpenShift AI 的竞品内容，生成结构化分析报告。

## 技术栈

- **后端**: Python + FastAPI + LangChain
- **前端**: React + Ant Design
- **Agent**: LangChain Multi-Agent (Analysis Agent + Predictor Agent)
- **部署**: Docker + Kubernetes

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/zhaomingkun1030/platform-oracle.git
cd platform-oracle
```

### 2. 配置环境

```bash
# 复制环境变量文件
cp backend/.env.example backend/.env

# 编辑配置
# LLM_API_URL: 大模型 API 地址
# LLM_API_KEY: API 密钥
# LLM_PROVIDER: google 或 azure
```

### 3. 本地运行

```bash
# 后端
cd backend
pip install -r requirements.txt
python main.py

# 前端
cd frontend
npm install
npm run dev
```

### 4. Docker 运行

```bash
docker build -t platform-oracle:latest .
docker run -p 8000:8000 -v $(pwd)/data:/data platform-oracle:latest
```

## 部署到 Kubernetes

```bash
kubectl apply -f k8s/
```

## 功能特性

- URL 分析：支持 OpenShift 官方文档和视频
- Multi-Agent 架构：Analysis Agent + Predictor Agent
- Excel 报告生成
- 手动触发执行
- JWT 认证

## 认证

- 用户名: admin
- 密码: admin123

## API 端点

- `POST /api/auth/login` - 登录
- `GET /api/analyses` - 获取分析记录
- `POST /api/analyses` - 创建新分析
- `DELETE /api/analyses/{id}` - 删除分析记录
- `GET /api/reports/{filename}` - 下载报告

## 项目结构

```
platform-oracle/
├── backend/           # 后端代码
│   ├── agents/       # Agent 实现
│   ├── api/          # API 路由
│   ├── services/     # 业务服务
│   └── main.py       # 入口文件
├── frontend/         # 前端代码
├── k8s/              # Kubernetes 配置
├── docker/          # Docker 配置
└── README.md
```
