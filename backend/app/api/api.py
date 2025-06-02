from fastapi import APIRouter

from .endpoints import knowledge, models, query

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(query.router, prefix="/chat", tags=["chat"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
