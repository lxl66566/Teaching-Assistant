import copy
import os

from surya.debug.draw import draw_polys_on_image
from surya.input.load import load_from_file
from surya.layout import LayoutPredictor


def visualize_layout_detection(pdf_path, output_dir=None, page_range=None):
    """
    对PDF文件应用Surya的布局检测，并将结果可视化保存为图片

    参数:
        pdf_path: PDF文件路径
        output_dir: 输出目录，默认为当前目录下的"layout_results"
        page_range: 要处理的页面范围，例如[0,1,2]表示处理前三页

    返回:
        保存的图片路径列表
    """
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "layout_results")
    os.makedirs(output_dir, exist_ok=True)

    # 加载PDF文件
    images, names = load_from_file(pdf_path, page_range)

    # 初始化布局检测器
    layout_predictor = LayoutPredictor()

    # 执行布局检测
    layout_predictions = layout_predictor(images)

    # 可视化结果并保存
    output_paths = []
    for idx, (image, layout_pred, name) in enumerate(
        zip(images, layout_predictions, names)
    ):
        # 获取多边形和标签
        polygons = [p.polygon for p in layout_pred.bboxes]
        labels = [
            f"{p.label}-{p.position}-{round(p.top_k[p.label], 2)}"
            for p in layout_pred.bboxes
        ]

        # 在图像上绘制多边形和标签
        bbox_image = draw_polys_on_image(
            polygons, copy.deepcopy(image), labels=labels, label_font_size=10
        )

        # 保存图像
        output_path = os.path.join(output_dir, f"{name}_{idx}_layout.png")
        bbox_image.save(output_path)
        output_paths.append(output_path)

        print(f"已保存第 {idx + 1} 页布局检测结果到: {output_path}")

    return output_paths


# 使用示例
if __name__ == "__main__":
    # 替换为您的PDF文件路径
    pdf_path = "test.pdf"
    # 可选：指定页面范围，例如处理前5页
    page_range = list(range(5))  # 或者设为None处理所有页面

    result_paths = visualize_layout_detection(pdf_path, page_range=page_range)
    print(f"总共生成了 {len(result_paths)} 个布局检测结果图像")
