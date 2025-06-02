import asyncio
import os
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import UploadFile
from loguru import logger

from ..config import settings
from ..database import get_standalone_db

# from ..database import get_db  # 移除 get_db 导入
from ..embedding import vector_db
from ..embedding.chunk import chunk_text
from ..embedding.doc_to_text_utils import process_file_to_text

# 全局字典，用于存储正在进行的文档处理任务
processing_tasks: Dict[str, asyncio.Task] = {}


class DocumentService:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """检查文件类型是否允许"""
        if not filename:
            return False
        return os.path.splitext(filename)[1].lower() in settings.ALLOWED_EXTENSIONS

    async def create_document(
        self,
        file: UploadFile,
        type: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """创建新文档记录"""
        if not file.filename:
            raise ValueError("文件名不能为空")

        document_id = str(uuid4())

        # 保存文件
        file_path = os.path.join(settings.UPLOAD_DIR, document_id)
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # 创建文档记录
        await self.db.execute(
            """
            INSERT INTO documents (
                id, filename, type, description,
                status, size
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                file.filename,
                type,
                description,
                "processing",
                len(content),
            ),
        )

        result = await self.get_document(document_id)
        if not result:
            raise FileNotFoundError(f"Failed to create document {document_id}")

        # 在后台启动文档处理任务并保存任务句柄
        task = asyncio.create_task(self.process_document(result))
        processing_tasks[document_id] = task

        return result

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档记录"""
        cursor = await self.db.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def list_documents(
        self,
        type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取文档列表"""
        query = ["SELECT * FROM documents WHERE 1=1"]
        params = []

        if type:
            query.append("AND type = ?")
            params.append(type)

        query.append("ORDER BY created_at DESC")

        # 获取文档列表
        cursor = await self.db.execute(" ".join(query), params)
        documents = [dict(row) for row in await cursor.fetchall()]

        return {
            "documents": documents,
        }

    async def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        document = await self.get_document(document_id)
        if not document:
            return False

        # 取消正在进行的文档处理任务
        if document_id in processing_tasks:
            task = processing_tasks.pop(document_id)
            if not task.done():
                task.cancel()
                try:
                    await task  # 等待任务取消完成
                except asyncio.CancelledError:
                    logger.warning(f"文档 {document_id} 的处理任务已取消。")

        await self.db.execute("DELETE FROM documents WHERE id = ?", (document_id,))

        # 删除文件
        file_path = os.path.join(settings.UPLOAD_DIR, document_id)
        if os.path.exists(file_path):
            os.remove(file_path)

        # 删除向量数据库中的文档块
        try:
            vector_db.remove(doc_id=document_id)
        except Exception as e:
            logger.error(f"删除向量数据库中的文档块失败: {e}")

        return True

    async def update_document(
        self,
        document_id: str,
        new_name: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新文档"""
        if not new_name and enabled is None:
            return await self.get_document(document_id)

        # 构建 UPDATE 语句和参数
        update_fields = []
        params = []

        if new_name:
            update_fields.append("filename = ?")
            params.append(new_name)

        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(enabled)

        # 添加 document_id 到参数列表
        params.append(document_id)

        # 构建完整的 SQL 语句
        sql = f"""
            UPDATE documents 
            SET {", ".join(update_fields)}
            WHERE id = ?
        """

        await self.db.execute(sql, params)
        return await self.get_document(document_id)

    async def process_document(self, document: Dict[str, Any]):
        """处理文档并在数据库中更新进度"""
        document_id = document["id"]
        db = None  # 初始化 db 为 None
        try:
            # 在后台任务中获取独立的数据库连接
            db = await get_standalone_db()

            # 模拟文档处理过程
            logger.info(f"开始处理文档: {document_id}, type: {document['type']}")
            text = await asyncio.to_thread(
                process_file_to_text,
                os.path.join(settings.UPLOAD_DIR, document_id),
                document["type"],
            )

            # 更新文档状态为 'embedding'
            await db.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                ("embedding", document_id),
            )
            await db.commit()  # 提交事务

            logger.info(f"文档 {document_id} 处理中，正在向向量数据库添加文档块...")
            chunked = chunk_text(text, max_chunk_size=700, overlap_size=50)

            await vector_db.add(texts=chunked, doc_id=document_id)

            logger.info(f"文档 {document_id} 处理完成，chunked_size: {len(chunked)}")

            # 更新文档状态为 'completed'
            await db.execute(
                "UPDATE documents SET status = ?, chunk_size = ? WHERE id = ?",
                ("completed", len(chunked), document_id),
            )
            await db.commit()  # 提交事务

            logger.info(f"文档 {document_id} 处理完成。")
        except asyncio.CancelledError:
            logger.warning(f"文档 {document_id} 的处理任务被取消。")
            if db:
                await db.execute(
                    "UPDATE documents SET status = ? WHERE id = ?",
                    ("cancelled", document_id),
                )
                await db.commit()  # 提交事务
        except Exception as e:
            # 如果处理失败，更新文档状态为 'failed'
            logger.error(f"文档 {document_id} 处理失败: {e}")
            if db:
                await db.execute(
                    "UPDATE documents SET status = ? WHERE id = ?",
                    ("failed", document_id),
                )
                await db.commit()  # 提交事务
        finally:
            # 无论成功、失败还是取消，都从全局字典中移除任务
            if document_id in processing_tasks:
                del processing_tasks[document_id]
            if db:
                await db.close()  # 关闭连接
