import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .api.api import api_router
from .config import settings
from .database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    try:
        # 启动时初始化数据库
        await init_db()
        yield
    except Exception as e:
        print(f"Error during database cleanup: {e}")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
    debug=True,
)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_STR)


# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# 健康检查
@app.get("/health")
async def health_check():
    """
    系统健康检查接口
    """
    return {"status": "healthy", "app_name": settings.APP_NAME}


# 前端静态文件服务
FRONTEND_DIST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"
)

if os.path.exists(FRONTEND_DIST_DIR) and os.path.isdir(FRONTEND_DIST_DIR):
    # 将 StaticFiles 放在所有 API 路由之后，并将其路径改为 "/"
    # html=True 会自动查找并提供 index.html
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
else:

    @app.get("/", response_class=HTMLResponse)
    async def frontend_not_found():
        """
        前端构建不存在时的提示
        """
        return HTMLResponse(
            content="Frontend build not found. Please build the frontend first.",
            status_code=404,
        )
