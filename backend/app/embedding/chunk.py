import logging as log

MAX_CHUNK_SIZE = 1024
OVERLAP_SIZE = 50


def chunk_text(
    text, max_chunk_size=MAX_CHUNK_SIZE, overlap_size=OVERLAP_SIZE
) -> list[str]:
    """
    将长文本按段落分割，并确保每个chunk不超过max_chunk_size，超长段落分割时添加overlap

    Args:
        text (str): 输入的文本
        max_chunk_size (int): 每个chunk的最大长度，默认为1000
        overlap_size (int): 超长段落分割时的重叠长度，默认为50

    Returns:
        list: 分割后的文本块列表
    """
    # 如果输入为空，返回空列表
    if not text or not isinstance(text, str):
        return []

    # 确保overlap_size不超过max_chunk_size
    overlap_size = min(overlap_size, max_chunk_size // 2)

    # 按行分割
    lines = text.split("\n")
    chunks = []

    for line in lines:
        # 移除首尾空白
        line = line.strip()
        if not line:
            continue

        # 如果行本身超过最大长度，则需要进一步分割并添加overlap
        if len(line) > max_chunk_size:
            start = 0
            while start < len(line):
                # 计算当前chunk的结束位置
                end = min(start + max_chunk_size, len(line))
                chunk = line[start:end]
                chunks.append(chunk)
                # 更新start位置，预留overlap
                start = end - overlap_size if end < len(line) else end
        else:
            # 如果行没有超过最大长度，则直接作为一个chunk
            chunks.append(line)

    log.debug(f"chunk 完成，分割后的文本块数量: {len(chunks)}")

    return chunks


# 示例用法
if __name__ == "__main__":
    # 测试文本
    sample_text = """-（转移导纳）4-e+ j6cj2c（电压比）\n的网络函\n以网络函数中（行a）的最高次方的次数来定义网络函数的阶"""

    # 分割文本
    result = chunk_text(sample_text, max_chunk_size=700, overlap_size=10)

    # 打印结果
    for i, chunk in enumerate(result):
        print(f"Chunk {i + 1} (length: {len(chunk)}):")
        print(chunk)
        print("-" * 50)
