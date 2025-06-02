from pathlib import Path

import fitz  # PyMuPDF


def is_text_pdf(pdf_path: Path | str, min_text_length: int = 50) -> bool:
    """
    判断一个 PDF 文件是否为“文字 PDF”。

    一个 PDF 被认为是“文字 PDF”，如果其所有非空白页中，包含显著文字的
    页面比例超过 50%。
    测试已通过。

    Args:
        pdf_path: PDF 文件的路径。
        min_text_length: 判断页面是否包含“显著文字”的最小文本长度阈值。
                         默认为 50 个字符（剥离空白符后）。

    Returns:
        如果 PDF 是文字 PDF，返回 True；否则返回 False。
        如果文件不存在、损坏或处理出错，也返回 False。
    """

    if isinstance(pdf_path, str):
        pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"错误: 文件未找到 -> {pdf_path}")
        return False

    total_non_blank_pages = 0
    pages_with_significant_text = 0

    try:
        # 使用 'with' 语句确保文件被正确关闭
        with fitz.open(pdf_path) as doc:
            if doc.page_count == 0:
                print(f"信息: PDF 文件不包含任何页面 -> {pdf_path}")
                return False  # 零页的 PDF 不算文字 PDF

            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)

                # 1. 提取文本并检查长度 (判断是否包含显著文字)
                text = page.get_text().strip()  # type: ignore
                has_significant_text = len(text) >= min_text_length

                # 2. 检查页面是否包含图片或图形 (判断是否为非空白页)
                # get_images(full=False) 更快，只检查是否存在图片对象
                has_images = len(page.get_images(full=False)) > 0
                has_drawings = len(page.get_drawings()) > 0

                # 如果页面包含显著文本 OR 图片 OR 图形，则认为它是非空白页
                is_non_blank = has_significant_text or has_images or has_drawings

                if is_non_blank:
                    total_non_blank_pages += 1
                    # 如果页面包含显著文本，则计数为有文字页
                    if has_significant_text:
                        pages_with_significant_text += 1

        # 计算比例
        if total_non_blank_pages == 0:
            # 如果总非空白页数为0 (意味着所有页面都是完全空白的)，
            # 则该 PDF 不被视为文字 PDF。
            print(f"信息: PDF 文件只包含空白页 -> {pdf_path}")
            return False

        percentage_text_pages = (
            pages_with_significant_text / total_non_blank_pages
        ) * 100

        # print(f"处理文件: {os.path.basename(pdf_path)}, 总页数: {doc.page_count}, 非空白页数: {total_non_blank_pages}, 显著文字页数: {pages_with_significant_text}, 比例: {percentage_text_pages:.2f}%") # 可选的调试输出

        # 判断比例是否超过 50%
        return percentage_text_pages > 50.0

    except fitz.FileDataError:
        print(f"错误: 无法打开或读取 PDF 文件 (文件可能损坏或加密) -> {pdf_path}")
        return False
    except Exception as e:
        print(f"处理文件时发生未知错误 {pdf_path}: {e}")
        return False
