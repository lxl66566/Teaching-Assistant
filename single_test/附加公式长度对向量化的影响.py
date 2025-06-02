import random
import string

import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.distance import cosine

# 注意：不再需要 requests 和 json 库用于 Ollama 交互

# --- Ollama 配置 ---
OLLAMA_BASE_URL = "http://127.0.0.1:11434"  # Ollama 服务的基础 URL
DEFAULT_OLLAMA_MODEL = "milkey/gte:large-zh-f16"  # 你在 Ollama 中使用的模型名
OLLAMA_CLIENT_TIMEOUT = 120  # Ollama client 的请求超时时间 (秒)

# 全局 ollama client 实例 (将在 main 函数中初始化)
ollama_client_instance = None

# --- 中文显示配置 (用于 Matplotlib) ---
try:
    plt.rcParams["font.sans-serif"] = [
        "SimHei"
    ]  # 或者 'Microsoft YaHei', 'WenQuanYi Micro Hei' 等
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
except Exception as e:
    print(f"设置中文字体失败: {e}。图表中的中文可能无法正常显示。")
    print("请确保已安装支持中文的字体，如 SimHei, Microsoft YaHei 等。")


def get_embedding(text: str, model: str = DEFAULT_OLLAMA_MODEL) -> np.ndarray | None:
    """
    从 Ollama API 获取文本的向量 (使用 ollama Python 库)。
    """
    global ollama_client_instance
    if ollama_client_instance is None:
        print("错误: Ollama client 未初始化。")
        return None

    try:
        # 使用 ollama client 的 embed 方法
        # 当 input 是单个字符串时, ollama client 返回 {'embedding': [float, ...]}
        response = ollama_client_instance.embed(model=model, input=text)

        if "embedding" in response:
            embedding_list = response["embedding"]
            return np.array(embedding_list, dtype=np.float32)
        else:
            # 尝试处理意外的响应格式，例如当 input 是列表时返回 'embeddings'
            if (
                "embeddings" in response
                and isinstance(response["embeddings"], list)
                and len(response["embeddings"]) > 0
            ):
                print(
                    f"警告: Ollama 为单个文本输入返回了 'embeddings' 列表，将使用第一个。响应: {response}"
                )
                embedding_list = response["embeddings"][0]
                return np.array(embedding_list, dtype=np.float32)

            print(f"错误：无法从 Ollama 响应中获取 'embedding'。响应: {response}")
            print(f'  模型: {model}, 文本 (前50字符): "{text[:50]}..."')
            return None
    except ImportError:  # 理论上 client 初始化时会捕获，但作为保障
        print(
            "错误：ollama Python 包未安装或无法导入。请运行 'pip install ollama' 安装。"
        )
        return None
    except Exception as e:
        print(f"使用 Ollama client 获取 embedding 失败: {e}")
        print(f'  模型: {model}, 文本 (前50字符): "{text[:50]}..."')
        print(
            f"  请确保 Ollama 服务正在运行于 {OLLAMA_BASE_URL}，模型 '{model}' 可用，"
        )
        print("  并且 ollama python 客户端版本与服务兼容。")
        return None


def generate_random_latex(length: int) -> str:
    """
    生成一个指定长度的、看起来像 LaTeX 的随机字符串。
    """
    if length <= 0:
        return ""

    chars = string.ascii_letters + string.digits + " "
    latex_elements = [
        "\\alpha",
        "\\beta",
        "\\gamma",
        "\\sum",
        "\\int",
        "\\frac",
        "\\sqrt",
        "_",
        "^",
        "{",
        "}",
        "(",
        ")",
        "[",
        "]",
        "+",
        "-",
        "=",
        "<",
        ">",
        "\\sin",
        "\\cos",
        "\\log",
        "\\lim",
        "\\partial",
        "\\nabla",
        "\\infty",
    ]

    formula = ""
    # 稍微调整生成逻辑，使其在长度较小时也能包含一些 LaTeX 元素
    use_latex_prob = (
        0.3 if length > 10 else 0.1
    )  # 长度较短时，减少latex元素概率避免元素过长

    while len(formula) < length:
        if random.random() > use_latex_prob or not latex_elements:
            formula += random.choice(chars)
        else:
            element = random.choice(latex_elements)
            if len(formula) + len(element) <= length + 3:  # 允许略微超出一点点
                formula += element
            else:  # 如果太长，就用单个字符填充
                if len(formula) < length:
                    formula += random.choice(chars)
                else:
                    break  # 避免死循环
    return formula[:length]


def main():
    global ollama_client_instance  # 声明我们要修改全局变量

    # 0. 初始化 Ollama Client
    try:
        from ollama import Client

        print(
            f"正在初始化 Ollama client (Host: {OLLAMA_BASE_URL}, Model: {DEFAULT_OLLAMA_MODEL}, Timeout: {OLLAMA_CLIENT_TIMEOUT}s)..."
        )
        ollama_client_instance = Client(
            host=OLLAMA_BASE_URL, timeout=OLLAMA_CLIENT_TIMEOUT
        )
        # 可以尝试 ping 一下服务或获取模型列表来验证连接
        ollama_client_instance.list()
        print("Ollama client 初始化成功并已连接到服务。")
    except ImportError:
        print("错误：ollama Python 包未安装。请运行 'pip install ollama' 安装。")
        print("程序终止。")
        return
    except Exception as e:
        print(f"初始化 Ollama client 或连接服务失败: {e}")
        print(f"请确保 Ollama 服务正在运行于 {OLLAMA_BASE_URL} 并且网络可达。")
        print("程序终止。")
        return
    print("-" * 30)

    # 1. 定义母句和句子 A
    mother_sentence = "在可变频的正弦电压源us激励下，由于感抗、容抗随频率变动，所以，电路中的电压、电流响应亦随频率变动。"
    sentence_a_base = "该电路由频率可调的正弦电压源us驱动。由于电感抗和电容抗会随着频率的变化而改变，因此电路中的电压和电流响应也会随之变化。"

    print(f"母句: {mother_sentence}")
    print(f"句子 A (基准): {sentence_a_base}")
    print("-" * 30)

    # 2. 获取母句的向量
    print(f"正在获取母句的向量 (模型: {DEFAULT_OLLAMA_MODEL})...")
    mother_vector = get_embedding(mother_sentence, model=DEFAULT_OLLAMA_MODEL)
    if mother_vector is None:
        print("无法获取母句向量，程序终止。")
        return
    print("母句向量获取成功。")
    print("-" * 30)

    formula_lengths = []
    distances = []

    # 3. 定义要测试的公式长度范围
    # latex_lengths_to_test = [0, 5, 10, 20, 30, 50, 75, 100, 150, 200, 250, 300]
    latex_lengths_to_test = sorted([*range(0, 400, 20), 5, 10, 15, 25, 30])

    print(f"将为句子 A 添加以下长度的 LaTeX 公式: {latex_lengths_to_test}")
    print("-" * 30)

    # 4. 生成子句，计算向量和距离
    for i, length in enumerate(latex_lengths_to_test):
        print(f"测试进度: {i + 1}/{len(latex_lengths_to_test)} (公式长度: {length})")

        if length == 0:
            child_sentence = sentence_a_base
            generated_formula = ""
        else:
            generated_formula = generate_random_latex(length)
            # child_sentence = f"{sentence_a_base} 公式内容： ${generated_formula}$" # 在公式前后加上 $ 符号
            child_sentence = f"{sentence_a_base} ${generated_formula}$"

        # 打印子句时限制长度，避免过长的公式刷屏
        display_child_sentence = child_sentence
        if len(display_child_sentence) > 100:
            display_child_sentence = display_child_sentence[:97] + "..."
        print(
            f'  子句: "{display_child_sentence}" (公式实际长度: {len(generated_formula)})'
        )

        child_vector = get_embedding(child_sentence, model=DEFAULT_OLLAMA_MODEL)

        if child_vector is not None and mother_vector is not None:
            # 确保两个向量都不是None且维度匹配 (通常embedding模型输出维度固定)
            if child_vector.shape == mother_vector.shape:
                distance = cosine(mother_vector, child_vector)
                formula_lengths.append(len(generated_formula))
                distances.append(distance)
                print(f"  与母句的向量余弦距离: {distance:.4f}")
            else:
                print(
                    f"  警告: 子句向量维度 ({child_vector.shape}) 与母句向量维度 ({mother_vector.shape}) 不匹配，跳过此数据点。"
                )
        else:
            print(
                f"  警告: 无法获取子句 (公式长度 {length}) 的向量，或母句向量无效，跳过此数据点。"
            )
        print("-" * 10)

    if not formula_lengths or not distances:
        print("没有成功计算任何距离，无法绘图。")
        return

    # 5. 绘制散点图
    plt.figure(figsize=(12, 7))  # 稍微增大图像尺寸
    plt.scatter(
        formula_lengths,
        distances,
        alpha=0.75,
        edgecolors="k",
        s=70,
        c="skyblue",
        linewidths=0.5,
    )

    plt.title(
        f"LaTeX 公式长度与向量余弦距离关系\n(Ollama 模型: {DEFAULT_OLLAMA_MODEL})",
        fontsize=15,
    )
    plt.xlabel("附加 LaTeX 公式的长度 (字符数)", fontsize=12)
    plt.ylabel("与母句的余弦距离 (越小越相似)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)

    # 在图上添加趋势线 (可选，如果数据点较多且有趋势)
    if len(formula_lengths) > 1:
        try:
            # 拟合一条一次多项式（直线）
            z = np.polyfit(formula_lengths, distances, 1)
            p = np.poly1d(z)
            plt.plot(
                sorted(formula_lengths),
                p(sorted(formula_lengths)),
                "r--",
                alpha=0.8,
                label=f"趋势线: y={z[0]:.4f}x+{z[1]:.4f}",
            )
            plt.legend()
        except Exception as e:
            print(f"绘制趋势线失败: {e}")

    plot_info = (
        f'母句 (部分): "{mother_sentence[:25]}..."\n'
        f'句子A (部分): "{sentence_a_base[:25]}..."\n'
        f"Ollama Host: {OLLAMA_BASE_URL}"
    )
    plt.figtext(
        0.5,
        -0.15,
        plot_info,
        ha="center",
        fontsize=9,
        bbox={"facecolor": "lightgrey", "alpha": 0.5, "pad": 5},
    )
    plt.subplots_adjust(bottom=0.28)  # 调整底部边距以容纳文本

    plt.show()


if __name__ == "__main__":
    main()
