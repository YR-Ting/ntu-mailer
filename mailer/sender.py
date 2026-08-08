"""
實際的 SMTP 寄信邏輯：組信件（含 CC/BCC、附件）、逐封寄送、回傳結果。
"""
import smtplib
import ssl
from dataclasses import dataclass
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from mailer.config import EmailAccount
from mailer.recipients import split_addresses
from mailer.template import render_content


@dataclass
class SendResult:
    email: str
    success: bool
    error: str = ""


def _build_message(
    account: EmailAccount,
    to_email: str,
    cc_list: list[str],
    subject: str,
    html_content: str,
    attachments: list,
) -> MIMEMultipart:
    msg = MIMEMultipart()
    # display_name 留空的話，formataddr 會自動只顯示信箱本身
    msg["From"] = formataddr((account.display_name, account.sender_email))
    msg["To"] = to_email
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    for att in attachments or []:
        # att 可以是 (filename, bytes) tuple，或有 .name / .read() 的檔案物件（如 Streamlit UploadedFile）
        if isinstance(att, tuple):
            filename, data = att
        else:
            filename, data = att.name, att.read()
        part = MIMEApplication(data, Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    return msg


def _connect(account: EmailAccount) -> smtplib.SMTP_SSL:
    context = ssl.create_default_context()
    conn = smtplib.SMTP_SSL(account.smtp_host, account.smtp_port, context=context, timeout=15)
    # 登入用 login_user（台大是學號本身，Gmail 是完整信箱），envelope/From 一律用完整 sender_email
    conn.login(account.login_user, account.sender_password)
    return conn


def send_one(
    account: EmailAccount,
    to_email: str,
    cc: str,
    bcc: str,
    subject: str,
    html_content: str,
    attachments: list = None,
    smtp_conn: smtplib.SMTP_SSL = None,
) -> SendResult:
    """
    寄出單一一封信。
    smtp_conn 可選：若在批次寄送時想重複使用同一條連線，可從外部傳入已登入的連線。
    """
    cc_list = split_addresses(cc)
    bcc_list = split_addresses(bcc)

    if account.bcc_self and account.sender_email not in bcc_list:
        bcc_list = bcc_list + [account.sender_email]

    all_recipients = [to_email] + cc_list + bcc_list

    msg = _build_message(account, to_email, cc_list, subject, html_content, attachments)

    owns_connection = smtp_conn is None
    try:
        if owns_connection:
            smtp_conn = _connect(account)

        # envelope sender 必須是完整格式（B12345678@ntu.edu.tw），不能只給學號，
        # 否則伺服器會回 504 5.5.2 need fully-qualified address
        smtp_conn.sendmail(account.sender_email, all_recipients, msg.as_string())
        return SendResult(email=to_email, success=True)

    except Exception as e:
        return SendResult(email=to_email, success=False, error=str(e))

    finally:
        if owns_connection and smtp_conn is not None:
            try:
                smtp_conn.quit()
            except Exception:
                pass


def send_batch(
    account: EmailAccount,
    recipients_df,
    subject: str,
    html_template: str,
    attachments: list = None,
    progress_callback=None,
) -> list[SendResult]:
    """
    批次寄送。共用同一條 SMTP 連線以加快速度。
    progress_callback(index, total, result)：每寄完一封就會呼叫一次，方便介面更新進度條。
    """
    results: list[SendResult] = []
    total = len(recipients_df)

    with _connect(account) as smtp_conn:
        for i, row in recipients_df.iterrows():
            row_dict = row.to_dict()
            personalized_html = render_content(html_template, row_dict)

            result = send_one(
                account=account,
                to_email=row_dict["email"],
                cc=row_dict.get("cc", ""),
                bcc=row_dict.get("bcc", ""),
                subject=subject,
                html_content=personalized_html,
                attachments=attachments,
                smtp_conn=smtp_conn,
            )
            results.append(result)

            if progress_callback:
                progress_callback(i + 1, total, result)

    return results
