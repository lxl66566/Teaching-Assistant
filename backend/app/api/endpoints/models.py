import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from ...database import get_db
from ...schemas.model import (
    CurrentModel,
    LocalModels,
    ModelConfigureRequest,
    ModelConfigureResponse,
    ModelDownloadProgress,
    ModelDownloadRequest,
    ModelDownloadResponse,
    ProviderList,
    ProviderModels,
    SearchModelsResponse,
)
from ...services.model_service import ModelService

router = APIRouter()


@router.get("/providers", response_model=ProviderList)
async def list_providers(db: aiosqlite.Connection = Depends(get_db)):
    """获取系统支持的所有模型服务商"""
    model_service = ModelService(db)
    try:
        providers = await model_service.get_providers()
        return {"provider": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers/{provider}", response_model=ProviderModels)
async def get_provider_models(
    provider: str, db: aiosqlite.Connection = Depends(get_db)
):
    """获取某个模型服务商的所有模型和其 api key"""
    model_service = ModelService(db)
    try:
        models = await model_service.get_provider_models(provider)
        api_key = await model_service.get_provider_api_key(provider)
        logger.info(f"获取模型服务商 {provider} 的模型列表和 api key {api_key} 成功")
        return {"model": models, "api_key": api_key}
    except ValueError as e:
        logger.error(f"400 获取模型服务商 {provider} 的模型失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"500 获取模型服务商 {provider} 的模型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local", response_model=LocalModels)
async def list_local_models(db: aiosqlite.Connection = Depends(get_db)):
    """获取本地所有模型"""
    model_service = ModelService(db)
    try:
        models = await model_service.get_local_models()
        return {"model": models}
    except Exception as e:
        logger.error(f"获取本地模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/configure", response_model=ModelConfigureResponse)
async def configure_model(
    request: ModelConfigureRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    """配置远程模型 API 密钥或本地模型"""
    model_service = ModelService(db)
    try:
        if request.type == "remote":
            if not request.provider or not request.api_key:
                raise HTTPException(
                    status_code=400,
                    detail="远程模型配置需要提供 provider 和 api_key",
                )

            await model_service.configure_remote_model_api_key(
                provider=request.provider,
                api_key=request.api_key,
            )

        elif request.type == "local":
            # 检查本地模型是否存在
            local_models = await model_service.get_local_models()
            logger.debug(f"本地模型列表: {local_models}")
            if request.name not in {model["name"] for model in local_models}:
                logger.error(f"404 本地模型 {request.name} 不存在")
                raise HTTPException(
                    status_code=404,
                    detail=f"本地模型 {request.name} 不存在",
                )

        # 设置为当前模型
        await model_service.set_current_model(
            model_type=request.type,
            model_name=request.name,
            provider=request.provider if request.type == "remote" else None,
        )

        return {"success": True, "message": "模型配置已更新"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/current", response_model=CurrentModel)
async def get_current_model(db: aiosqlite.Connection = Depends(get_db)):
    """获取当前模型配置"""
    model_service = ModelService(db)
    try:
        current = await model_service.get_current_model()
        if not current:
            return {"type": "null"}

        return {
            "type": current.type,
            "name": current.name,
            "provider": current.provider,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取当前模型配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=SearchModelsResponse)
async def search_models(
    query: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    """搜索可下载的模型"""
    model_service = ModelService(db)
    try:
        models = await model_service.search_models(query)
        return {"models": models}
    except Exception as e:
        logger.error(f"搜索模型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download", response_model=ModelDownloadResponse)
async def download_model(
    request: ModelDownloadRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    """开始下载模型"""
    model_service = ModelService(db)
    try:
        await model_service.start_model_download(
            name=request.name,
        )
        return {"success": True, "message": "开始下载模型"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{model_name}/progress", response_model=ModelDownloadProgress)
async def get_download_progress(
    model_name: str,
    db: aiosqlite.Connection = Depends(get_db),
):
    """获取模型下载进度"""
    model_service = ModelService(db)
    try:
        progress = await model_service.get_download_progress(model_name)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
