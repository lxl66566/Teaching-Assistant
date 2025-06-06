import asyncio
import logging as log
from typing import Optional

import chromadb

# ChromaDB 提供了 SentenceTransformer 的集成，简化嵌入过程
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)

from ..config import settings


class Embedding:
    def __init__(self, collection_name="rag_collection") -> None:
        log.info("初始化 ChromaDB 客户端...")

        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DIRECTORY))
        embedding_function = OllamaEmbeddingFunction(
            url=f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            model_name=settings.EMBEDDING_MODEL_NAME,
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,  # type: ignore
        )
        self.add_lock = asyncio.Lock()

    async def add(self, texts: list[str], doc_id: str):
        batch_size = settings.EMBEDDING_BATCH_SIZE
        # 为每个文本生成唯一的 ID
        ids = [f"{doc_id}_{i}" for i in range(len(texts))]

        # 为每个文本添加 doc_id 元数据
        metadatas = [{"doc_id": doc_id} for _ in texts]

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_texts = texts[i : i + batch_size]
            batch_metadatas = metadatas[i : i + batch_size]

            async with self.add_lock:
                await asyncio.to_thread(
                    self.collection.add,
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas,  # type: ignore
                )

    def remove(self, doc_id: str):
        self.collection.delete(where={"doc_id": doc_id})

    def query(
        self,
        query_texts: list[str],
        n_results: int = 5,
        included_doc_ids: Optional[list[str]] = None,
    ):
        # 构建查询条件
        where_condition = None
        if included_doc_ids is not None:
            where_condition = {"doc_id": {"$in": included_doc_ids}}

        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where_condition,  # type: ignore
            include=["documents"],
        )

        return results


vector_db = Embedding()
