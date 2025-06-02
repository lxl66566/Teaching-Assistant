import asyncio
import re
from typing import Awaitable, List, Tuple

from loguru import logger

from ..utils.llm_utils import flatten_svg_in_markdown
from . import llm


async def process_text_with_svg_generation(
    text: str,
) -> str:
    """
    在输入文本中提取所有 ```img...``` 内部的内容，通过生成函数，并将结果替换回原文本。

    Args:
        text (str): 待处理的输入字符串。

    Returns:
        str: 替换所有 img 标签后的结果字符串。
    """
    max_concurrent_tasks: int = 5
    # 使用 re.DOTALL 模式匹配多行内容
    img_pattern = re.compile(
        r"(?s)(```img)(.*?)(```)"
    )  # 修正：为了方便替换，把开始标签的 `>` 分离出来

    # 找到所有匹配项
    matches = list(img_pattern.finditer(text))

    if not matches:
        logger.info("未找到任何 img 标签。")
        return text

    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    # 存储需要替换的信息：(原始匹配的开始索引, 原始匹配的结束索引, 新的SVG内容)
    replacement_tasks: List[Awaitable[Tuple[int, int, str]]] = []

    async def process_single_svg_match(match: re.Match) -> Tuple[int, int, str]:
        """处理单个 img 匹配的协程。"""
        # match.group(0) 是整个匹配的字符串
        # match.group(1) 是 ```img 部分
        # match.group(2) 是内部内容
        # match.group(3) 是 ```

        full_match_start = match.start(0)
        full_match_end = match.end(0)
        img_inner_content = match.group(2)  # 提取 img 内部的内容

        async with semaphore:  # 使用信号量限制并发
            try:
                # 调用传入的 generate_img 函数处理内部内容
                processed_svg_string = await generate_svg(img_inner_content)
                return (full_match_start, full_match_end, processed_svg_string)
            except Exception as e:
                logger.error(
                    f"⚠️ 处理 SVG 内容 '{img_inner_content[:50]}...' 时发生错误: {e}"
                )
                # 发生错误时，保留原始 SVG 标签或返回一个错误提示 SVG
                # 这里我们选择保留原始标签
                return (full_match_start, full_match_end, match.group(0))

    # 为每个匹配项创建一个任务
    for match in matches:
        replacement_tasks.append(process_single_svg_match(match))

    # 并发执行所有任务
    # asyncio.gather 会等待所有任务完成，并收集结果
    processed_results = await asyncio.gather(*replacement_tasks)

    # 构建新的字符串
    # 最佳实践是收集所有字符串片段，然后一次性 join 它们，以提高效率
    # processed_results 包含 (start_index, end_index, new_content)
    # 确保它们按原始顺序排列，以便正确拼接
    processed_results.sort(key=lambda x: x[0])

    parts = []
    last_end_index = 0
    for start_index, end_index, new_content in processed_results:
        # 添加上一个匹配结束到当前匹配开始之间的文本
        parts.append(text[last_end_index:start_index])
        # 添加处理后的新内容
        parts.append(new_content)
        last_end_index = end_index

    # 添加最后一个匹配结束到文本末尾的文本
    parts.append(text[last_end_index:])

    return "".join(parts)


async def generate_svg(prompt: str) -> str:
    """
    生成 SVG 图像。

    Args:
        prompt (str): 输入提示语。

    Returns:
        str: 生成的 SVG 图像。
    """
    logger.info("开始生成 SVG 图像：" + prompt)
    result = await llm.async_generate(
        messages=[
            {
                "role": "system",
                "content": "请你根据我的描述，为我生成一个准确的 SVG 图像。只输出 SVG 本身，不要输出其他任何内容。如果描述是教学相关内容，请默认使用中国标准。例如，电阻应该是长方体而不是折线。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )
    result = result.strip().removeprefix("```svg").removesuffix("```")
    result = flatten_svg_in_markdown(result)
    return result
