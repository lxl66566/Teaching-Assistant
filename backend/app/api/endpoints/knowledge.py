import os
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from loguru import logger

from ...config import settings
from ...database import get_db
from ...schemas import document as schemas
from ...services.document_service import DocumentService

router = APIRouter()


@router.post("/upload", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    type: str = Form(...),
    description: Optional[str] = Form(None),
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    上传文档到知识库
    """
    service = DocumentService(db)

    # 添加日志记录
    logger.info(f"正在上传文件: {file.filename}, 类型: {type}, 大小: {file.size}")

    # 检查文件名是否存在
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 检查文件类型
    if not service.is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {os.path.splitext(file.filename)[1]}",
        )

    # 获取文件大小
    try:
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # 重置文件指针
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")

    # 检查文件大小
    if file_size == 0:
        raise HTTPException(status_code=400, detail="文件大小为0")

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制: {file_size} > {settings.MAX_UPLOAD_SIZE}",
        )

    try:
        return await service.create_document(
            file=file,
            type=type,
            description=description,
        )
    except Exception as e:
        logger.error(f"创建文档失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建文档失败: {str(e)}")


@router.get("/status/{document_id}", response_model=schemas.Document)
async def get_document_status(
    document_id: str, db: aiosqlite.Connection = Depends(get_db)
):
    """
    获取文档处理状态
    """
    service = DocumentService(db)
    document = await service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document


@router.get("/list", response_model=schemas.DocumentList)
async def list_documents(
    type: Optional[str] = None,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    获取知识库文档列表
    """
    service = DocumentService(db)
    return await service.list_documents(
        type=type,
    )


@router.delete("/{document_id}", response_model=schemas.DocumentDelete)
async def delete_document(document_id: str, db: aiosqlite.Connection = Depends(get_db)):
    """
    删除知识库文档
    """
    service = DocumentService(db)
    success = await service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "message": "文档已成功删除"}


@router.put("/{document_id}", response_model=schemas.Document)
async def update_document(
    document_id: str,
    update_data: schemas.DocumentUpdate,
    db: aiosqlite.Connection = Depends(get_db),
):
    """
    更新知识库文档
    """
    service = DocumentService(db)
    document = await service.update_document(
        document_id, new_name=update_data.new_name, enabled=update_data.enabled
    )
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document
