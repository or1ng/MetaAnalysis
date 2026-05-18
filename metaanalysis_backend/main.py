"""
MetaAnalysis元析智能 - 后端入口
技术栈：Python + FastAPI + SQLAlchemy + SQLite(开发) / MySQL(生产)
"""
import json
import math
import traceback

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import init_db
from core.exceptions import AppException
from config.settings import get_settings

# 导入路由模块
from api.auth import router as auth_router
from api.upload import router as upload_router
from api.clean import router as clean_router
from api.ai_chat import router as ai_router
from api.statistic import router as stat_router
from api.chart import router as chart_router
from api.report import router as report_router
from api.user import router as user_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    await init_db()
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"[MetaAnalysis] {settings.APP_NAME} started")
    yield
    print("[MetaAnalysis] shutdown")


def _json_default(obj):
    """Custom JSON encoder: NaN/Inf -> None, numpy types -> native"""
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    try:
        import numpy as np
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            v = float(obj)
            return None if (math.isnan(v) or math.isinf(v)) else v
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
    except ImportError:
        pass
    return str(obj)


class SafeJSONResponse(JSONResponse):
    """JSONResponse that handles NaN/Inf values"""
    def render(self, content) -> bytes:
        cleaned = self._clean_nan(content)
        return json.dumps(
            cleaned,
            default=_json_default,
            ensure_ascii=False,
        ).encode("utf-8")

    @staticmethod
    def _clean_nan(obj):
        """Recursively clean NaN/Inf from data structure"""
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: SafeJSONResponse._clean_nan(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [SafeJSONResponse._clean_nan(v) for v in obj]
        try:
            import numpy as np
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                v = float(obj)
                if math.isnan(v) or math.isinf(v):
                    return None
                return v
        except ImportError:
            pass
        return obj


app = FastAPI(
    title=settings.APP_NAME,
    description="国内首款集成统计学内核+AI推理+自动化数据治理的新一代智能数据分析平台",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(clean_router)
app.include_router(ai_router)
app.include_router(stat_router)
app.include_router(chart_router)
app.include_router(report_router)
app.include_router(user_router)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for debugging"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print(f"[ERROR] {type(exc).__name__}: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": str(exc), "data": None},
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.code if exc.code >= 400 else 400,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}
