from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont

# 初始化 PaddleOCR
ocr = PaddleOCR(
    lang="ch",
    det_model_dir="ch_PP-OCRv4_det_infer",  # 指定检测模型路径，如果不存在会自动下载
    rec_model_dir="ch_PP-OCRv4_rec_infer",  # 指定识别模型路径，如果不存在会自动下载
)  # need to run only once to load model into memory

img_path = "Z:/test.png"
# 获取原始图片尺寸
with Image.open(img_path) as img:
    width, height = img.size

# 创建一个新的空白图片
new_img = Image.new("RGB", (width, height), color="white")
draw = ImageDraw.Draw(new_img)

# 设置字体，请确保系统中有这个字体文件，否则需要修改为其他可用字体
try:
    font = ImageFont.truetype("simhei.ttf", 14)  # 使用黑体，大小为20
except:
    font = ImageFont.load_default()  # 如果没有找到字体，使用默认字体

# OCR识别
result = ocr.ocr(img_path)

# 在新图片上绘制文字
for idx in range(len(result)):
    res = result[idx]
    for line in res:
        # 获取文本和位置
        points = line[0]
        text = line[1][0]

        # 计算文本位置（使用检测框的左上角坐标）
        x = int(points[0][0])
        y = int(points[0][1])

        # 绘制文字
        draw.text((x, y), text, font=font, fill="black")

# 保存结果图片
new_img.save("result.png")
