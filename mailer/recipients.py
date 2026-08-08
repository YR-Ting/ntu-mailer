"""
讀取與驗證收件人 CSV 清單。
CSV 欄位：name, email 為必填；cc, bcc 為選填（多筆用空格分隔）。
其餘任意欄位都可以在 content.html 內用 $欄位名 替換。
"""
import pandas as pd

REQUIRED_COLUMNS = ["name", "email"]
RESERVED_COLUMNS = ["email", "cc", "bcc"]  # 不可用於內文變數替換

NTU_DOMAIN = "ntu.edu.tw"


def normalize_ntu_address(value: str) -> str:
    """
    若 value 不含 '@'，視為台大學號，自動補上 @ntu.edu.tw。
    已包含 '@' 的地址（不管哪個網域）維持原樣，不強制改成台大信箱。
    """
    value = value.strip()
    if not value:
        return value
    if "@" not in value:
        return f"{value}@{NTU_DOMAIN}"
    return value


def _normalize_column(series: pd.Series, use_ntu_shorthand: bool) -> pd.Series:
    if not use_ntu_shorthand:
        return series
    return series.apply(
        lambda raw: " ".join(normalize_ntu_address(v) for v in raw.split())
        if raw
        else raw
    )


def load_recipients(csv_file, use_ntu_shorthand: bool = True) -> pd.DataFrame:
    """
    csv_file: 檔案路徑字串，或 Streamlit file_uploader 回傳的檔案物件
    use_ntu_shorthand: 若為 True，email/cc/bcc 欄位中只填學號（不含 @）的值，
                        會自動補上 @ntu.edu.tw。使用 Gmail 寄送時通常應設為 False，
                        因為收件人不一定是台大信箱。
    回傳：整理好的 DataFrame，並保證含有 cc / bcc 欄位（缺的話補空字串）
    """
    df = pd.read_csv(csv_file, dtype=str).fillna("")

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"CSV 缺少必要欄位：{', '.join(missing)}")

    for col in ("cc", "bcc"):
        if col not in df.columns:
            df[col] = ""

    df["email"] = _normalize_column(df["email"], use_ntu_shorthand)
    df["cc"] = _normalize_column(df["cc"], use_ntu_shorthand)
    df["bcc"] = _normalize_column(df["bcc"], use_ntu_shorthand)

    if df["email"].str.strip().eq("").any():
        bad_rows = df[df["email"].str.strip().eq("")].index.tolist()
        raise ValueError(f"以下列的 email 欄位是空的（第 {bad_rows} 列，從 0 起算）")

    return df


def split_addresses(raw: str) -> list[str]:
    """把 'a@x.com b@y.com' 這種空格分隔字串拆成 email 清單，並過濾空字串。"""
    if not raw:
        return []
    return [addr.strip() for addr in raw.split() if addr.strip()]
