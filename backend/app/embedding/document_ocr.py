import json
import os
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
from rapidocr import RapidOCR
from surya.layout import LayoutPredictor

# 全局初始化 OCR 和布局检测器，避免重复加载模型
# 注意：模型下载可能需要时间
# 建议在首次运行时确保模型已下载或手动下载并指定路径

# 初始化 RapidOCR
# RapidOCR 默认会下载模型，如果需要指定模型路径，可以参考其文档
ocr = RapidOCR(str((Path("__file__").parent / "config.yaml").absolute()))

# 初始化布局检测器
layout_predictor = LayoutPredictor()


def _render_pdf_page_to_image(document, page_num):
    """
    辅助函数：将单个 PDF 页面渲染为 PIL Image。
    """
    page = document.load_page(page_num)
    pix = page.get_pixmap(dpi=300)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # type: ignore


def _perform_ocr_on_cropped_image(cropped_image: Image.Image):
    """
    辅助函数：对裁剪后的图片执行 OCR。
    """
    result = ocr(cropped_image)  # type: ignore
    if isinstance(result.txts, Iterable):  # type: ignore
        return str("".join(result.txts))  # type: ignore
    else:
        return str(result)


def ocr_pdf_pages(pdf_path: str) -> dict[int, list[str]]:
    """
    对 PDF 文件的每一页进行布局检测（串行）和 OCR（并行）。

    参数:
        pdf_path: PDF 文件路径。

    返回:
        一个字典，键为页码（从0开始），值为该页的 OCR 结果列表。
        每个结果是一个字典，包含 'bbox' (边界框) 和 'text' (识别文本)。
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    document = fitz.open(pdf_path)
    total_pages = document.page_count
    all_ocr_futures = []
    # 存储 (page_num, original_bbox) 对应 future 的索引
    future_to_bbox_map = {}
    current_future_index = 0

    print("Starting layout detection and parallel OCR...")
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        for page_num in range(total_pages):
            print(f"Processing page {page_num + 1}/{total_pages}...")
            pil_image = _render_pdf_page_to_image(document, page_num)

            layout_predictions = layout_predictor([pil_image], batch_size=1)
            if not layout_predictions:
                continue

            layout_pred = layout_predictions[0]

            for bbox_pred in layout_pred.bboxes:
                if bbox_pred.label != "Text":
                    continue

                x_min, y_min, x_max, y_max = bbox_pred.bbox
                cropped_image = pil_image.crop((x_min, y_min, x_max, y_max))

                # 提交 OCR 任务到线程池
                future = executor.submit(_perform_ocr_on_cropped_image, cropped_image)
                all_ocr_futures.append(future)
                future_to_bbox_map[future] = (
                    page_num,
                    [x_min, y_min, x_max, y_max],
                    current_future_index,
                )
                current_future_index += 1

    document.close()

    print(f"Waiting for {len(all_ocr_futures)} OCR tasks to complete...")
    ocr_results_flat = []
    for future in as_completed(all_ocr_futures):
        page_num, bbox, original_index = future_to_bbox_map[future]
        try:
            recognized_text = future.result()
            assert isinstance(recognized_text, str)
            ocr_results_flat.append((original_index, page_num, bbox, recognized_text))
        except Exception as exc:
            print(
                f"OCR for region {bbox} on page {page_num} generated an exception: {exc}"
            )
            ocr_results_flat.append((original_index, page_num, bbox, ""))

    # 将扁平化的 OCR 结果重组回按页码和边界框的结构
    sorted_ocr_results_flat = sorted(ocr_results_flat, key=lambda x: x[0])
    final_ocr_results = {i: [] for i in range(total_pages)}

    for _, page_num, bbox, recognized_text in sorted_ocr_results_flat:
        final_ocr_results[page_num].append(recognized_text)

    print("OCR process completed.")
    # 按页码排序结果
    sorted_results = {k: final_ocr_results[k] for k in sorted(final_ocr_results.keys())}
    return sorted_results


if __name__ == "__main__":
    res = ocr_pdf_pages("test.pdf")
    json.dump(res, open("test.json", "w", encoding="utf-8"), ensure_ascii=False)
