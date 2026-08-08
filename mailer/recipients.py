"""
讀取與驗證收件人 CSV 清單。
CSV 欄位：name, email 為必填；cc, bcc 為選填（多筆用空格分隔）。
其餘任意欄位都可以在 content.html 內用 $欄位名 替換。
"""
import pandas as pd

REQUIRED_COLUMNS = ["name", "email"]
RESERVED_COLUMNS = ["email", "cc", "bcc"]  # 不可用於內文變數替換


def load_recipients(csv_file) -> pd.DataFrame:
    """
    csv_file: 檔案路徑字串，或 Streamlit file_uploader 回傳的檔案物件
    回傳：整理好的 DataFrame，並保證含有 cc / bcc 欄位（缺的話補空字串）
    """
    df = pd.read_csv(csv_file, dtype=str).fillna("")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"CSV 缺少必要欄位：{', '.join(missing)}")

    if df["email"].str.strip().eq("").any():
        bad_rows = df[df["email"].str.strip().eq("")].index.tolist()
        raise ValueError(f"以下列的 email 欄位是空的（第 {bad_rows} 列，從 0 起算）")

    # 沒有 cc / bcc 欄位就補上空字串，方便後面統一處理
    for col in ("cc", "bcc"):
        if col not in df.columns:
            df[col] = ""

    return df


def split_addresses(raw: str) -> list[str]:
    """把 'a@x.com b@y.com' 這種空格分隔字串拆成 email 清單，並過濾空字串。"""
    if not raw:
        return []
    return [addr.strip() for addr in raw.split() if addr.strip()]
