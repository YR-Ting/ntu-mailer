# NTU Mailer（網頁介面版）

給系學會使用的批次寄信工具，本機執行的網頁介面。

## 安裝

```
pip install -r requirements.txt
```

## 密碼設定（擇一）

**方法一：直接在網頁上輸入**（最簡單，不用額外設定）
啟動後在「寄件帳號設定」區塊輸入帳號密碼即可，密碼只存在當次執行的記憶體中。

**方法二：用 .env 檔案**（不想每次都手動輸入）
1. 複製 `.env.example`，改名為 `.env`
2. 填入你的帳號密碼
3. `.env` 已加入 `.gitignore`，不會被上傳或分享出去，請勿手動移除這個保護

## 啟動

```
streamlit run app.py
```

瀏覽器會自動開啟 http://localhost:8501

## 收件人 CSV 格式

參考 `recipients_sample.csv`：

| 欄位 | 必填 | 說明 |
|---|---|---|
| name | 是 | 收件人姓名，可在內文用 $name 替換 |
| email | 是 | 收件人信箱 |
| cc | 否 | 副本信箱，多筆用空格分隔 |
| bcc | 否 | 密件副本信箱，多筆用空格分隔 |

其餘自訂欄位（如 `department`）也可以加進 CSV，並在內文用 `$department` 替換。

## 專案結構

```
ntu_mailer_project/
├── app.py                  # Streamlit 介面
├── mailer/
│   ├── config.py            # 帳號設定資料結構
│   ├── recipients.py        # CSV 讀取與驗證
│   ├── template.py          # 內文變數替換
│   └── sender.py            # SMTP 寄信邏輯
├── requirements.txt
├── .env.example
└── recipients_sample.csv
```

## 安全性注意事項

- 密碼絕不寫死在程式碼裡，只透過表單輸入或 `.env` 讀取
- `.env` 已加入 `.gitignore`，分享專案給其他系學會成員時不會外洩密碼
- 本工具是本機執行（localhost），密碼不會經過任何外部伺服器
- 正式寄送前務必先用「測試寄送」確認格式與內文替換正確

CONTACT B14601012@ntu.edu.tw
