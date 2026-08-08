"""
處理內文中的 $欄位名 變數替換，例如 $name -> 該收件人的姓名。
以及把使用者直接打字按 Enter 產生的換行符號，轉成正確的 HTML 換行，
確保「使用者打字看到的樣子」跟「實際寄出信件的樣子」一致。
"""
import re
from string import Template

from mailer.recipients import RESERVED_COLUMNS


def normalize_line_breaks(content: str) -> str:
    """
    把使用者直接打字產生的換行（\\n）轉成 HTML 看得懂的換行：
    - 連續空行（段落間空一行）→ 段落間距（用兩個 <br> 呈現，行為貼近 Gmail 打字習慣）
    - 單一 Enter → <br>
    使用者若自己用格式工具列插入的 <p>、<div> 等區塊標籤，其內部換行不受影響，
    因為這裡只處理標籤與標籤「之間」的純文字換行，不會去拆解既有標籤內容。
    """
    # 統一換行符號（Windows 的 CRLF 轉成 LF），避免重複計算
    content = content.replace("\r\n", "\n")
    # 連續兩個以上換行 → 視為分段，轉成雙倍 <br> 呈現段落間距
    content = re.sub(r"\n{2,}", "<br><br>", content)
    # 剩下的單一換行 → 一般換行
    content = content.replace("\n", "<br>")
    return content


def render_content(html_template: str, row: dict) -> str:
    """
    html_template: 使用者在網頁上輸入的內文（可能是純文字加上工具列插入的 HTML 標籤）
    row: 該收件人這一列的資料（dict 形式，例如 {"name": "小明", "email": "..."}）
    """
    safe_values = {
        key: value for key, value in row.items() if key not in RESERVED_COLUMNS
    }
    # Template 對找不到的變數預設會報錯，用 safe_substitute 改成保留原樣，避免整批寄送中斷
    substituted = Template(html_template).safe_substitute(safe_values)
    return normalize_line_breaks(substituted)
