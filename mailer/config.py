"""
帳號與 SMTP 設定的資料結構。
其他模組需要帳號資訊時，統一使用這個類別，避免到處重複寫欄位。
"""
from dataclasses import dataclass


@dataclass
class EmailAccount:
    smtp_host: str          # 例如 smtps.ntu.edu.tw 或 smtp.gmail.com
    smtp_port: int          # 例如 465
    login_user: str         # SMTP 登入帳號。台大通常只需學號本身（例如 B12345678）；Gmail 則是完整信箱
    sender_email: str       # 完整寄件信箱地址，envelope sender 必須是完整格式，例如 B12345678@ntu.edu.tw
    sender_password: str    # 登入密碼（Gmail 請用「應用程式密碼」，不要用一般登入密碼）
    display_name: str = ""  # 收件人看到的寄件者名稱，留空則顯示原始信箱地址
    bcc_self: bool = False  # 是否在每封信自動 BCC 一份給自己，作為寄件備份


# 兩種常見服務的預設 SMTP 設定，方便介面切換時自動帶入
NTU_SMTP_HOST = "smtps.ntu.edu.tw"
NTU_SMTP_PORT = 465

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 465
