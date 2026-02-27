"""
Platform Oracle - OpenShift 竞品分析智能体系统
主入口文件
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext
from datetime import timedelta

# 导入 Agent
from agents.analysis_agent import AnalysisAgent
from agents.predictor_agent import PredictorAgent
from services.url_fetcher import URLFetcher
from services.excel_generator import ExcelGenerator

# 加载环境变量
load_dotenv()

# 初始化
app = FastAPI(title="Platform Oracle API", version="1.0.0")
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
DATA_DIR = Path("/data")
CONFIG_DIR = DATA_DIR / "config"
RUNS_DIR = DATA_DIR / "runs"
REPORTS_DIR = DATA_DIR / "reports"

# 确保目录存在
for d in [DATA_DIR, CONFIG_DIR, RUNS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "platform-oracle-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# 模型配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")
LLM_API_URL = os.getenv("LLM_API_URL", "http://localhost:8000/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")


# ==================== 数据模型 ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AnalysisRequest(BaseModel):
    url: str = Field(..., description="要分析的 URL")
    analyst: str = Field(default="admin", description="分析人员")


class AnalysisResponse(BaseModel):
    id: str
    url: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    report_file: Optional[str] = None


class AnalysisRecord(BaseModel):
    id: str
    url: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    analyst: str
    report_file: Optional[str] = None


# ==================== 工具函数 ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


def load_runs() -> List[Dict]:
    runs_file = RUNS_DIR / "runs.json"
    if runs_file.exists():
        with open(runs_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_runs(runs: List[Dict]):
    runs_file = RUNS_DIR / "runs.json"
    with open(runs_file, "w", encoding="utf-8") as f:
        json.dump(runs, f, ensure_ascii=False, indent=2)


# ==================== Agent 实现 ====================

class CompetitorAnalysisSystem:
    """竞品分析系统"""
    
    def __init__(self):
        self.analysis_agent = AnalysisAgent(
            provider=LLM_PROVIDER,
            api_url=LLM_API_URL,
            api_key=LLM_API_KEY,
            model=LLM_MODEL
        )
        self.predictor_agent = PredictorAgent(
            provider=LLM_PROVIDER,
            api_url=LLM_API_URL,
            api_key=LLM_API_KEY,
            model=LLM_MODEL
        )
        self.url_fetcher = URLFetcher()
        self.excel_generator = ExcelGenerator()
    
    async def analyze(self, url: str, analyst: str) -> Dict[str, Any]:
        """执行分析"""
        start_time = datetime.now().isoformat()
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 1. 获取 URL 内容
            content = await self.url_fetcher.fetch(url)
            
            # 2. Analysis Agent 分析
            analysis_result = await self.analysis_agent.analyze(content, url)
            
            # 3. Predictor Agent 预测
            predictor_result = await self.predictor_agent.predict(analysis_result)
            
            # 4. 生成 Excel 报告
            report_filename = f"report_{analysis_id}.xlsx"
            report_path = REPORTS_DIR / report_filename
            
            self.excel_generator.generate(
                analysis_result=analysis_result,
                predictor_result=predictor_result,
                output_path=str(report_path),
                url=url,
                analyst=analyst
            )
            
            end_time = datetime.now().isoformat()
            
            return {
                "id": analysis_id,
                "url": url,
                "status": "completed",
                "start_time": start_time,
                "end_time": end_time,
                "analyst": analyst,
                "report_file": report_filename,
                "analysis": analysis_result,
                "prediction": predictor_result
            }
            
        except Exception as e:
            end_time = datetime.now().isoformat()
            return {
                "id": analysis_id,
                "url": url,
                "status": "failed",
                "start_time": start_time,
                "end_time": end_time,
                "analyst": analyst,
                "error": str(e)
            }


# 初始化系统
analysis_system = CompetitorAnalysisSystem()


# ==================== API 路由 ====================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """登录"""
    # 硬编码 admin/admin123
    if request.username == "admin" and request.password == "admin123":
        access_token = create_access_token(
            data={"sub": request.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        return LoginResponse(access_token=access_token)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password"
    )


@app.get("/api/analyses", response_model=List[AnalysisRecord])
async def get_analyses(token: dict = Depends(verify_token)):
    """获取分析记录"""
    runs = load_runs()
    return [
        AnalysisRecord(
            id=run["id"],
            url=run["url"],
            status=run["status"],
            start_time=run["start_time"],
            end_time=run.get("end_time"),
            analyst=run["analyst"],
            report_file=run.get("report_file")
        )
        for run in runs
    ]


@app.post("/api/analyses", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    token: dict = Depends(verify_token)
):
    """创建新分析"""
    # 执行分析
    result = await analysis_system.analyze(request.url, request.analyst)
    
    # 保存记录
    runs = load_runs()
    runs.insert(0, {
        "id": result["id"],
        "url": result["url"],
        "status": result["status"],
        "start_time": result["start_time"],
        "end_time": result.get("end_time"),
        "analyst": result["analyst"],
        "report_file": result.get("report_file")
    })
    save_runs(runs)
    
    return AnalysisResponse(
        id=result["id"],
        url=result["url"],
        status=result["status"],
        start_time=result["start_time"],
        end_time=result.get("end_time"),
        report_file=result.get("report_file")
    )


@app.delete("/api/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    token: dict = Depends(verify_token)
):
    """删除分析记录"""
    runs = load_runs()
    runs = [r for r in runs if r["id"] != analysis_id]
    save_runs(runs)
    return {"status": "deleted"}


@app.get("/api/reports/{filename}")
async def download_report(
    filename: str,
    token: dict = Depends(verify_token)
):
    """下载报告"""
    report_path = REPORTS_DIR / filename
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(report_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
