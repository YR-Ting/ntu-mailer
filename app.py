"""
NTU Mailer - 網頁介面
只負責畫面與使用者互動，實際寄信邏輯都在 mailer/ 套件底下。
"""
import json
import os

import streamlit as st
from dotenv import load_dotenv

from mailer.backup import build_eml_zip, build_log_csv
from mailer.config import (
    EmailAccount,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
    NTU_SMTP_HOST,
    NTU_SMTP_PORT,
)
from mailer.recipients import load_recipients
from mailer.sender import BatchConnectionError, send_batch, send_one
from mailer.template import render_content

load_dotenv()  # 本機執行時讀取同目錄下的 .env 檔案（若有的話）

TUTORIAL_URL = "https://YR-Ting.github.io/ntu-mailer/tutorial.html"  # 部署 GitHub Pages 後請替換成實際網址


def get_secret(key: str, default: str = "") -> str:
    """
    統一的設定值讀取方式：
    - 部署在 Streamlit Cloud 時，優先讀取 Settings → Secrets 設定的值
    - 本機執行時，讀取 .env 檔案（或環境變數）
    - 兩者都沒有就回傳 default，讓使用者自己在網頁上輸入
    """
    if key in st.secrets:
        return st.secrets[key]
    return os.getenv(key, default)


st.set_page_config(page_title="NTU Mailer", page_icon="📧")
st.title("📧 NTU Mailer")
st.caption("批次寄送信件工具 — 系學會專用")


# ---------- 1. 帳號設定 ----------
st.header("1. 寄件帳號設定")

use_gmail = st.toggle("使用 Gmail 寄送（關閉則使用台大信箱）", value=False)

if use_gmail:
    st.caption(
        "Gmail 登入請使用「應用程式密碼」，不要用一般登入密碼。"
        "設定方式：Google 帳戶 → 安全性 → 兩步驟驗證（需先開啟）→ 應用程式密碼。"
    )
    default_host, default_port = GMAIL_SMTP_HOST, GMAIL_SMTP_PORT
    login_label = "Gmail 完整信箱地址"
else:
    st.caption("台大信箱登入帳號為學號本身，不需加上 @ntu.edu.tw。")
    st.warning(
        "台大信箱寄信伺服器僅允許校內網路連線。若你不在校園網路，"
        "請先連上台大 VPN 或校內網路（ntu_peap, eduroam）再寄信，"
        "否則會出現連線逾時的錯誤。"
    )
    default_host, default_port = NTU_SMTP_HOST, NTU_SMTP_PORT
    login_label = "台大學號"

col1, col2 = st.columns(2)
with col1:
    login_user = st.text_input(
        login_label, value=get_secret("MAIL_LOGIN_USER", "")
    )
    if use_gmail:
        sender_email = login_user  # Gmail 登入帳號本身就是完整信箱
    else:
        sender_email = st.text_input(
            "完整寄件信箱地址（例如 B12345678@ntu.edu.tw）",
            value=(f"{login_user}@ntu.edu.tw" if login_user else ""),
            help="伺服器要求寄件地址必須是完整格式，不能只填學號。",
        )
    display_name = st.text_input(
        "寄件顯示名稱（選填，留空則顯示原始信箱地址）", value=""
    )
with col2:
    sender_password = st.text_input(
        "密碼",
        value=get_secret("MAIL_PASSWORD", ""),
        type="password",
        help="密碼只會存在這次執行的記憶體中，關閉程式即消失，不會被儲存或上傳。"
        "若管理員已在 Secrets 設定好帳密，這裡會自動帶入，一般使用者不需要自己填。",
    )
    smtp_host = st.text_input("SMTP 主機", value=default_host)
    smtp_port = st.number_input("SMTP 連接埠", value=default_port)

account = EmailAccount(
    smtp_host=smtp_host,
    smtp_port=int(smtp_port),
    login_user=login_user,
    sender_email=sender_email,
    sender_password=sender_password,
    display_name=display_name,
)


# ---------- 2. 收件人清單 ----------
st.header("2. 收件人清單")

col_upload, col_sample = st.columns([3, 1])
with col_upload:
    csv_file = st.file_uploader("上傳收件人 CSV", type=["csv"])
    st.caption(
        "CSV 需包含 email 欄位（必填）；name、cc、bcc 為選填（cc/bcc 多筆信箱請用空格分隔）。"
        "其餘欄位可在內文中用 $欄位名 替換，例如 $name。"
        " **若收件人是台大信箱，email/cc/bcc 欄位可以只填學號，會自動補上 @ntu.edu.tw（無論你用台大信箱或 Gmail 寄送皆適用）。**"
    )
    st.markdown(f"📘 [查看詳細教學（附圖文說明）]({TUTORIAL_URL})")
with col_sample:
    st.write("")  # 對齊用的空行
    st.write("")
    sample_csv_path = os.path.join(os.path.dirname(__file__), "recipients_sample.csv")
    if os.path.exists(sample_csv_path):
        with open(sample_csv_path, "rb") as f:
            st.download_button(
                "📄 下載範例 CSV",
                data=f.read(),
                file_name="recipients_sample.csv",
                mime="text/csv",
            )

recipients_df = None
if csv_file is not None:
    try:
        # 學號簡寫規則看的是「收件人」是不是台大人，跟寄件帳號用台大信箱或 Gmail 無關，
        # 所以一律套用；已包含 @ 的地址不受影響，維持原樣。
        recipients_df = load_recipients(csv_file, use_ntu_shorthand=True)
        st.success(f"成功讀取 {len(recipients_df)} 筆收件人")
        st.dataframe(recipients_df, use_container_width=True)
    except ValueError as e:
        st.error(str(e))


# ---------- 3. 信件內容 ----------
st.header("3. 信件內容")

subject = st.text_input("信件主旨", value="")

DEFAULT_CONTENT = "親愛的 $name 您好，<br><br>"

st.caption(
    "直接打字、按 Enter 換行，跟 Gmail 撰寫信件一樣。"
    "可用 $name 等變數，會依 CSV 每一列自動替換成對應的值。"
)

if "mail_html_content" not in st.session_state:
    st.session_state["mail_html_content"] = DEFAULT_CONTENT

# 這個隱藏欄位是編輯器與系統之間真正儲存內容的地方，使用者不會直接看到它，
# 只是透過下方的 JS 把 contenteditable 編輯區的內容同步進來。
SYNC_LABEL = "⧉mail_content_sync⧉"

current_content_json = json.dumps(st.session_state["mail_html_content"])

editor_html = f"""
<style>
  html, body {{ background:#ffffff; margin:0; padding:0; }}
</style>
<div style="margin-bottom:8px;display:flex;flex-wrap:wrap;gap:4px;font-family:sans-serif;">
  <button onclick="document.execCommand('bold')" title="粗體" type="button" style="font-weight:bold;">B</button>
  <button onclick="document.execCommand('italic')" title="斜體" type="button" style="font-style:italic;">I</button>
  <button onclick="document.execCommand('underline')" title="底線" type="button" style="text-decoration:underline;">U</button>
  <button onclick="document.execCommand('strikeThrough')" title="刪除線" type="button" style="text-decoration:line-through;">S</button>
  <input type="color" title="文字顏色" onchange="document.execCommand('foreColor', false, this.value)" style="width:30px;height:30px;padding:0;border:1px solid #ccc;">
  <select onchange="if(this.value) document.execCommand('fontSize', false, this.value); this.selectedIndex=0;" title="字級" style="height:30px;">
    <option value="">字級</option>
    <option value="2">小</option>
    <option value="3">中</option>
    <option value="5">大</option>
    <option value="7">特大</option>
  </select>
  <button onclick="document.execCommand('justifyLeft')" title="靠左對齊" type="button">⯇</button>
  <button onclick="document.execCommand('justifyCenter')" title="置中" type="button">☰</button>
  <button onclick="document.execCommand('justifyRight')" title="靠右對齊" type="button">⯈</button>
  <button onclick="var u=prompt('輸入超連結網址：','https://');if(u)document.execCommand('createLink', false, u)" title="插入超連結" type="button">🔗</button>
  <button onclick="var u=prompt('輸入圖片網址：');if(u)document.execCommand('insertImage', false, u)" title="插入圖片" type="button">🖼️</button>
  <button onclick="document.execCommand('insertUnorderedList')" title="項目符號" type="button">☰•</button>
  <button onclick="document.execCommand('removeFormat')" title="清除格式" type="button">✕</button>
</div>
<div id="editor" contenteditable="true"
     style="min-height:220px;max-height:420px;overflow-y:auto;border:1px solid #ccc;
            border-radius:4px;padding:12px;font-family:sans-serif;font-size:14px;
            background:white;color:black;line-height:1.5;">
</div>
<script>
  const editor = document.getElementById("editor");
  editor.innerHTML = {current_content_json};

  function findSyncTextarea() {{
    const areas = window.parent.document.querySelectorAll("textarea");
    for (const el of areas) {{
      if (el.getAttribute("aria-label") === "{SYNC_LABEL}") return el;
    }}
    return null;
  }}

  let syncTimer = null;
  function syncToStreamlit() {{
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => {{
      const target = findSyncTextarea();
      if (!target) return;
      const setter = Object.getOwnPropertyDescriptor(
        window.parent.HTMLTextAreaElement.prototype, "value"
      ).set;
      setter.call(target, editor.innerHTML);
      target.dispatchEvent(new Event("input", {{ bubbles: true }}));
    }}, 600);
  }}

  editor.addEventListener("input", syncToStreamlit);
  editor.addEventListener("blur", syncToStreamlit);
</script>
"""

st.components.v1.html(editor_html, height=400, scrolling=True)

# 隱藏欄位：實際儲存內容的地方，用 CSS 藏起來，只留給上方編輯器的 JS 讀寫。
st.markdown(
    f'<style>textarea[aria-label="{SYNC_LABEL}"] {{ display: none; }}</style>',
    unsafe_allow_html=True,
)
html_content = st.text_area(
    SYNC_LABEL, key="mail_html_content", label_visibility="collapsed"
)

with st.expander("進階：直接編輯 HTML 原始碼"):
    st.caption("與上方編輯器共用同一份內容；在這裡修改後，重新整理頁面即可反映到上方視覺化編輯器。")
    st.code(html_content, language="html")

with st.expander("📧 預覽套用變數後的樣子（以 $name = 測試 為例）"):
    preview_html = render_content(html_content, {"name": "測試", "email": ""})
    st.components.v1.html(
        f"""
        <html>
        <head>
        <style>
            html, body {{ background:#ffffff; margin:0; padding:0; }}
        </style>
        </head>
        <body>
            <div style="font-family:sans-serif;font-size:14px;color:#000000;
                        background:#ffffff;padding:12px;">
                {preview_html}
            </div>
        </body>
        </html>
        """,
        height=250,
        scrolling=True,
    )

uploaded_attachments = st.file_uploader(
    "附件（可選，可多選）", accept_multiple_files=True
)


# ---------- 4. 測試寄送 ----------
st.header("4. 測試寄送")
st.caption("先寄一封給自己確認格式與內文替換是否正確，再進行正式寄送。")

test_email = st.text_input("測試信箱（收件人只會是這個信箱）", value=sender_email)

if st.button("🧪 寄送測試信"):
    if not login_user or not sender_password:
        st.error("請先填寫寄件帳號與密碼")
    elif not test_email:
        st.error("請填寫測試信箱")
    else:
        test_row = {"name": "測試", "email": test_email}
        if recipients_df is not None and len(recipients_df) > 0:
            test_row = recipients_df.iloc[0].to_dict()

        rendered = render_content(html_content, test_row)

        with st.spinner("寄送中..."):
            result = send_one(
                account=account,
                to_email=test_email,
                cc="",
                bcc="",
                subject=subject,
                html_content=rendered,
                attachments=uploaded_attachments,
            )

        if result.success:
            st.success(f"測試信已寄出至 {test_email}")
        else:
            st.error(
                f"寄送失敗：{result.error}\n\n"
                "常見原因：帳號密碼錯誤（Gmail 請確認是否用「應用程式密碼」而非一般登入密碼）、"
                "或台大信箱需連上校內網路／VPN。"
            )


# ---------- 5. 正式批次寄送 ----------
st.header("5. 正式批次寄送")

confirm = st.checkbox("我已確認測試信正常，要正式寄送給所有收件人")

if st.button("🚀 正式寄送", disabled=not confirm):
    if recipients_df is None or len(recipients_df) == 0:
        st.error("請先上傳收件人 CSV")
    elif not login_user or not sender_password:
        st.error("請先填寫寄件帳號與密碼")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_area = st.container()

        def on_progress(i, total, result):
            progress_bar.progress(i / total)
            status_text.text(f"寄送中... {i}/{total}")
            with result_area:
                if result.success:
                    st.write(f"✅ {result.email}")
                else:
                    st.write(f"❌ {result.email} — {result.error}")

        try:
            with st.spinner("批次寄送中，請勿關閉視窗..."):
                results = send_batch(
                    account=account,
                    recipients_df=recipients_df,
                    subject=subject,
                    html_template=html_content,
                    attachments=uploaded_attachments,
                    progress_callback=on_progress,
                )
        except BatchConnectionError as e:
            st.error(
                f"❌ {e}\n\n"
                "常見原因：帳號密碼錯誤（Gmail 請確認是否用「應用程式密碼」而非一般登入密碼）、"
                "或台大信箱需連上校內網路／VPN。"
            )
            st.stop()

        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        st.info(f"寄送完成：成功 {success_count} 封，失敗 {fail_count} 封")

        # 存進 session_state：因為下方的下載按鈕本身也會觸發頁面重新執行，
        # 若不保存，results 這個區域變數會在下一次重新執行時消失，備份區塊就會跟著不見。
        st.session_state["last_send_results"] = results

if "last_send_results" in st.session_state:
    results = st.session_state["last_send_results"]

    st.subheader("📦 寄件備份下載")
    st.caption("不再透過 BCC 寄回信箱，改為以下檔案供留存查閱。")

    col_csv, col_eml = st.columns(2)
    with col_csv:
        st.download_button(
            "⬇️ 下載寄送記錄（CSV）",
            data=build_log_csv(results),
            file_name="send_log.csv",
            mime="text/csv",
        )
    with col_eml:
        st.download_button(
            "⬇️ 下載完整信件備份（ZIP）",
            data=build_eml_zip(results),
            file_name="sent_emails_backup.zip",
            mime="application/zip",
            help="包含每封信的完整原始內容（.eml 檔），可用 Outlook / Thunderbird 等信箱軟體開啟查看。",
        )
