"""
把批次寄送結果輸出成本機檔案，作為寄件備份，取代原本的 BCC 寄回自己信箱的方式。
輸出兩種檔案：
1. CSV 記錄：時間、收件人、主旨、成功與否、錯誤訊息（一目了然的總表）
2. ZIP 壓縮檔：內含每封信的完整 .eml 原始內容（可用信箱軟體開啟，查看實際寄出的信件外觀）
"""
import csv
import io
import zipfile

from mailer.sender import SendResult


def build_log_csv(results: list[SendResult]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["寄送時間", "收件人", "主旨", "狀態", "錯誤訊息"])
    for r in results:
        writer.writerow(
            [r.sent_at, r.email, r.subject, "成功" if r.success else "失敗", r.error]
        )
    return buffer.getvalue().encode("utf-8-sig")  # utf-8-sig 讓 Excel 開啟中文不會亂碼


def build_eml_zip(results: list[SendResult]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, r in enumerate(results, start=1):
            if not r.raw_message:
                continue
            status = "ok" if r.success else "failed"
            safe_email = r.email.replace("@", "_at_")
            filename = f"{i:03d}_{status}_{safe_email}.eml"
            zf.writestr(filename, r.raw_message)
    return buffer.getvalue()
