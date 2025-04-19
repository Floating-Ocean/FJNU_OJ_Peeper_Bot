import os
from pathlib import Path

import imgkit
import markdown2
from lxml import html

from src.render.html.css import get_basic_css, load_css


def _fill_in_html(body: str, css: str, body_extra: str = "") -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            {get_basic_css()}
            {css}
        </style>
    </head>
    <body>
        <div class="content">
            {body}
            {body_extra}
        </div>
    </body>
    </html>
    """


def md_to_html(markdown_path: str, css_path: str, extra_body: str = "") -> str:
    with open(markdown_path, "r", encoding="utf-8") as f:
        md_html = markdown2.markdown(f.read())

    md_dir = os.path.dirname(markdown_path)
    md_dir_path = Path(md_dir).resolve()

    tree = html.fromstring(md_html)
    prefix = md_dir_path.as_uri() + "/"

    for img in tree.xpath('//img'):
        src = img.get('src')
        if src and not src.startswith(('http://', 'https://', '/')):
            img.set('src', prefix + src)  # 替换相对路径为绝对路径

    html_body = html.tostring(tree, encoding='unicode')
    html_css = load_css(css_path)

    return _fill_in_html(html_body, html_css, extra_body)


def render_md_html(markdown_path: str, css_path: str, output_path: str, extra_body: str = ""):
    md_html = md_to_html(markdown_path, css_path, extra_body)
    options = {
        'enable-local-file-access': None,   # 允许本地文件访问
        'encoding': "UTF-8",                # 强制指定编码
        'width': '1088',
        'disable-smart-width': None,        # 禁用自动宽度调整
        'quality': '100',                   # 图片质量（避免压缩失真）
        'format': 'png'                     # 明确指定输出格式
    }
    imgkit.from_string(md_html, output_path, options=options)
