import os
from datetime import datetime

from src.core.constants import Constants
from src.render.html.markdown import md_to_html, render_md_html

_lib_path = os.path.join(Constants.config["lib_path"], "How-To-Cook")
_css_path = os.path.join(_lib_path, "style", "index.css")


def render_how_to_cook(dish_path: str, output_path: str):
    extra_body = f"""
        <div class="copyright">
            <div class="tool-container">
                <p class="tool-name">How to Cook</p>
                <p class="tool-version">v1.4.0</p>
            </div>
            <p class="generation-info">Generated at {datetime.now().strftime("%Y/%m/%d %H:%M:%S")}.<br>
                                       Initiated by OBot\'s ACM {Constants.core_version}.<br>
                                       Wish you everything goes well.</p>
        </div>
        """
    md_html = md_to_html(dish_path, _css_path, extra_body)
    render_md_html(dish_path, _css_path, output_path, extra_body)
