import asyncio
import re

import requests
import wikipedia
from loguru import logger

from ..embedding import vector_db


async def get_wikipedia_content(keyword, lang="zh") -> str:
    """
    根据给定的关键词从维基百科获取百科内容。

    Args:
        keyword (str): 要搜索的词。
        lang (str): 维基百科的语言代码，例如 "zh" (中文), "en" (英文)。
                    默认值为 "zh"。

    Returns:
        str: 维基百科页面的纯文本内容，如果页面不存在或发生其他错误则返回错误信息。
    """

    try:
        wikipedia.set_lang(lang)
    except ValueError:
        return f"无效的语言代码: '{lang}'。请使用有效的维基百科语言代码（例如 'zh', 'en', 'zh-cn' 等）。"

    try:
        content = requests.get(
            f"https://pure.md/https://{lang}.wikipedia.org/wiki/{keyword}"
        ).text
        if not content:
            raise Exception("维基百科页面为空。")
        return content.replace(r"\[编辑\]", "").replace("\n\n\n", "\n\n")
    except Exception as puree:
        logger.error(f"pure.md 请求失败: {puree}, fallback to wikipedia.page")
        try:
            page = wikipedia.page(keyword, auto_suggest=True, redirect=True)
            return re.sub(r"\n\s+", " ", page.content)
        except wikipedia.exceptions.PageError:
            return f"找不到 '{keyword}' 的维基百科页面。"
        except wikipedia.exceptions.DisambiguationError as e:
            return f"'{keyword}' 是一个消歧义页面。可能的选项包括: {e.options}\n请尝试提供更具体的关键词。"
        except wikipedia.exceptions.HTTPTimeoutError:
            return "请求维基百科时发生HTTP超时错误。请检查您的网络连接。"
        except Exception as e:
            logger.error(f"发生未知错误: {e}")
            return str(e)


async def query_vector_db(query_texts: list[str], n_results: int = 5) -> str:
    """
    从向量数据库中查询与 query_texts 距离最近（最相关）的文本内容。
    注意：查询到的内容可能是 OCR 得来，可能含有错误的文本或乱码，不保证正确性。

    Args:
        query_texts (list[str]): 查询文本列表。
        n_results (int, optional): 查询结果数量。默认为 5。

    Returns:
        str: 合并的查询结果。
    """

    results = vector_db.query(query_texts, n_results)
    if results and results.get("ids") and results["ids"][0]:
        return "\n".join(
            [results["documents"][0][i] for i in range(len(results["ids"][0]))]  # type: ignore
        )
    else:
        return "未找到相关内容"


# 示例用法
if __name__ == "__main__":
    search_term = "方解石"

    content = asyncio.run(get_wikipedia_content(search_term))

    if content:
        print("\n--- 维基百科内容 ---")
        print(content)
    else:
        print("未能获取维基百科内容。")
