"""
處理內文中的 $欄位名 變數替換，例如 $name -> 該收件人的姓名。
"""
from string import Template

from mailer.recipients import RESERVED_COLUMNS


def render_content(html_template: str, row: dict) -> str:
    """
    html_template: content.html 的原始內容（字串）
    row: 該收件人這一列的資料（dict 形式，例如 {"name": "小明", "email": "..."}）
    """
    safe_values = {
        key: value for key, value in row.items() if key not in RESERVED_COLUMNS
    }
    # Template 對找不到的變數預設會報錯，用 safe_substitute 改成保留原樣，避免整批寄送中斷
    return Template(html_template).safe_substitute(safe_values)
