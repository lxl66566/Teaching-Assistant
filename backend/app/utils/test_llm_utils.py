from .llm_utils import flatten_svg_in_markdown


def test_flatten_svg_in_markdown():
    s = """
其他内容
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
    <path d="1 2 3"/>
</svg>
其他内容
"""
    assert (
        flatten_svg_in_markdown(s)
        == """
其他内容
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="1 2 3"/></svg>
其他内容
"""
    )
