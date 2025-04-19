import os
import re
from pathlib import Path
from re import Match


def get_basic_css():
    return """
    body {
        margin: 0; 
        padding: 20px;
        background: white;
    }
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 10px auto 10px 0;
    }
    """


def load_css(css_path: str) -> str:
    css_dir = os.path.dirname(css_path)
    css_dir_path = Path(css_dir).resolve()

    prefix = css_dir_path.as_uri() + "/"

    def _replace_css_url(match: str | Match[str]) -> str:
        relative_path = match.group(1)
        if relative_path.startswith(('http://', 'https://', 'data:', 'file://')):
            return f'url({relative_path})'  # 跳过绝对路径

        relative_path = relative_path.strip('\'"')  # 处理路径中的特殊符号（如空格）
        abs_path = prefix + relative_path

        return f'url("{abs_path}")'

    # 正则匹配所有url(...)引用
    pattern = re.compile(r'url\(\s*[\'"]?(.*?)[\'"]?\s*\)', re.IGNORECASE)

    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    return pattern.sub(_replace_css_url, css_content)
