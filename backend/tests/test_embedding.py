import time

import chromadb
from app.embedding import Embedding


async def test_chroma_embedding():
    em = Embedding("test")

    LONG_ACADEMIC_TEXT = """
    向量数据库是专门设计用于存储、管理和搜索高维向量数据的数据库系统。这些向量通常是机器学习模型（特别是深度学习模型，如BERT、GPT或图像识别模型）生成的嵌入（Embeddings）。嵌入是将非结构化数据（如文本、图像、音频）转换为稠密数字向量的过程，使得语义上相似的对象在向量空间中彼此靠近。

    传统的关系型数据库或文档数据库主要处理结构化或半结构化数据，并使用精确匹配或基于关键词的搜索。然而，它们不适合高效地执行基于相似性的向量搜索（如k-NN，k近邻搜索或ANN，近似最近邻搜索）。向量数据库通过优化索引结构（如HNSW、IVF、LSH）和查询算法来解决这个问题，能够在数十亿级别的向量数据集中实现毫秒级的相似性搜索。

    在学术研究领域，向量数据库的应用日益广泛。例如，在自然语言处理（NLP）中，研究人员使用向量数据库存储论文摘要、段落或句子的嵌入，以快速查找相关研究、进行文献综述或发现新的研究方向。在生物信息学中，蛋白质序列或基因表达数据的向量表示可以存储在向量数据库中，用于查找相似的生物序列或模式。计算机视觉研究者也利用它来索引大规模图像或视频数据集的特征向量，实现内容相似的图像检索。

    构建一个有效的向量索引需要考虑几个关键因素：选择合适的嵌入模型至关重要，模型的质量直接影响向量表示的语义准确性；文本分块（Chunking）策略对长文本的处理尤为重要，需要平衡块大小和上下文信息，避免信息丢失或分割不当；索引参数（如HNSW的ef_construction和M值）的选择会影响索引构建时间和查询性能/召回率的权衡。针对特定领域（如学术论文），可能需要微调嵌入模型或采用特殊的预处理/分块方法，以更好地捕捉领域术语和复杂关系。
    """

    WRONG_TEXT = """这是一个错误的文本，用于混淆"""

    text_chunks = [x for x in LONG_ACADEMIC_TEXT.split("\n") if x.strip()]

    print("开始向 ChromaDB 添加文档块并生成嵌入...")
    start_time = time.time()
    await em.add(texts=text_chunks, doc_id="1")
    await em.add(texts=[WRONG_TEXT], doc_id="2")
    index_time = time.time() - start_time
    print(
        f"索引构建完成，添加了 {len(text_chunks) + 1} 个文档块，耗时: {index_time:.2f} 秒"
    )
    print(f"集合中文档总数: {em.collection.count()}")

    query_text = "错误文本用于混淆"
    print(f"\n执行查询: '{query_text}'")
    start_time = time.time()
    results: chromadb.QueryResult = em.query(
        query_texts=[query_text],
        n_results=3,
        included_doc_ids=["1"],
    )
    query_time = time.time() - start_time

    print(f"\n查询结果 (耗时: {query_time:.4f} 秒):")
    print(results)
    print("尝试提取")
    if results and results.get("ids") and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            print(f"  --- 结果 {i + 1} ---")
            print(f"  ID: {results['ids'][0][i]}")
            print(f'  文本块内容:\n"""\n{results["documents"][0][i]}\n"""')  # type: ignore
    else:
        raise ValueError("查询没有返回结果。")
