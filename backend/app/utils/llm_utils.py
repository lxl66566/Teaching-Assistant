import re


def remove_think(text: str) -> str:
    """
    删除文本中的"思考"部分
    """
    return text.replace("<think>", "").replace("</think>", "")


def flatten_svg_in_markdown(markdown_string: str) -> str:
    """
    将 Markdown 字符串中所有的 <svg>...</svg> 元素转换为一行。

    移除 <svg> 标签和 </svg> 标签之间内容的所有空白字符。

    Args:
        markdown_string: 包含 Markdown 和潜在 SVG 元素的字符串。

    Returns:
        处理后的 Markdown 字符串，其中 SVG 元素被压缩到一行。
    """

    # 正则表达式解释:
    # (<svg.*?>)  : 捕获组 1。匹配 <svg 后跟着任意数量的非换行字符（.`*?`)
    #               直到第一个 `>`。这会匹配完整的开标签，包括属性。
    # (.*?)       : 捕获组 2。匹配开标签 `>` 后和闭标签 `</svg>` 前的
    #               任意字符 (`.`) 任意次数 (`*`)，非贪婪 (`?`)。
    #               re.S 标志确保 `.` 也匹配换行符。这是 SVG 内容部分。
    # (</svg>)    : 捕获组 3。匹配字面量 </svg> 闭标签。
    # re.S        : 标志，使 `.` 匹配包括换行符在内的所有字符。这对于多行 SVG 内容至关重要。
    svg_pattern = re.compile(r"(<svg.*?>.*?</svg>)", re.S)

    def replace_svg_content(match):
        """
        re.sub 的回调函数，用于处理每个匹配到的 SVG 块。
        """
        # match.group(1) 是开标签 (<svg ... >)
        # match.group(2) 是 SVG 内容 (开标签和闭标签之间的内容)
        # match.group(3) 是闭标签 (</svg>)
        svg_region = match.group(1)

        cleaned_content = re.sub(r">[\s\n]+<", "><", svg_region)
        return cleaned_content

    # 使用 re.sub 替换所有匹配到的 SVG 块
    # replace_svg_content 函数会被应用于每个匹配项
    transformed_string = svg_pattern.sub(replace_svg_content, markdown_string)

    return transformed_string
