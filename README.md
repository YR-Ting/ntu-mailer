# NTU Mailer（網頁介面版）

給系學會使用的批次寄信工具，本機執行的網頁介面，支援台大信箱與 Gmail 雙寄件來源。

**Contact：** B14601012@ntu.edu.tw

## 安裝

```
pip install -r requirements.txt
```

## 密碼設定（擇一）

**方法一：直接在網頁上輸入**（最簡單，不用額外設定）
啟動後在「寄件帳號設定」區塊輸入帳號密碼即可，密碼只存在當次執行的記憶體中，關閉程式即消失。

**方法二：用 `.env` 檔案**（不想每次都手動輸入）
1. 複製 `.env.example`，改名為 `.env`
2. 填入你的帳號密碼
3. `.env` 已加入 `.gitignore`，不會被上傳或分享出去，請勿手動移除這個保護

## 啟動

```
streamlit run app.py
```

瀏覽器會自動開啟 http://localhost:8501

## 兩種寄件來源

| | 台大信箱 | Gmail |
|---|---|---|
| 登入帳號 | 學號本身（例如 `B12345678`，不加 `@ntu.edu.tw`） | 完整信箱地址 |
| 密碼 | 信箱登入密碼 | 應用程式密碼（需先開啟兩步驟驗證） |
| SMTP 主機 | smtps.ntu.edu.tw:465 | smtp.gmail.com:465 |

介面上方的 toggle 開關可以切換兩者，切換後會自動帶入對應的 SMTP 設定。

**寄件地址規則：** 台大 SMTP 伺服器要求信封上的寄件地址（envelope sender）必須是完整格式（`學號@ntu.edu.tw`），只填學號會被拒絕（`Sender address rejected` 錯誤）。因此介面把「登入帳號」與「完整寄件信箱」拆成兩個欄位分開處理。

## 收件人 CSV 格式

上傳區旁邊有「下載範例 CSV」按鈕可以直接參考，格式如下：

| 欄位 | 必填 | 說明 |
|---|---|---|
| email | 是 | 收件人信箱。若對方是台大信箱，可只填學號，系統會自動補上 `@ntu.edu.tw` |
| name | 否 | 收件人姓名，可在內文用 `$name` 替換 |
| cc | 否 | 副本信箱，多筆用空格分隔 |
| bcc | 否 | 密件副本信箱，多筆用空格分隔 |

其餘自訂欄位（如 `department`）也可以加進 CSV，並在內文用 `$department` 替換。

## 詳細圖文教學（GitHub Pages）

`docs/tutorial.md` 是給一般使用者看的圖文教學（含 CSV 填寫、帳號設定、VPN 提醒）。要讓 `app.py` 裡「查看詳細教學」的連結生效，需要開啟 GitHub Pages：

1. 到 repo 的 Settings → Pages
2. Source 選 `Deploy from a branch`，Branch 選 `main`，資料夾選 `/docs`，儲存
3. 幾分鐘後會產生網址，類似 `https://你的帳號.github.io/ntu-mailer/tutorial`
4. 把這個網址填回 `app.py` 最上方的 `TUTORIAL_URL` 變數，重新 commit / push
5. 教學裡提到的截圖（`docs/images/` 資料夾）目前是佔位說明，請自行截圖實際操作畫面後放入對應檔名

## 收件人 CSV 學號簡寫

使用台大信箱寄送時（Gmail 開關關閉），CSV 的 `email`、`cc`、`bcc` 欄位可以只填學號（例如 `B12345678`），系統會自動補上 `@ntu.edu.tw`。已包含 `@` 的地址則維持原樣。使用 Gmail 寄送時，因收件人不一定是台大信箱，不會套用這個自動補齊規則，請填完整信箱地址。

## 寄件備份

正式寄送完成後，畫面會提供兩個下載按鈕：
- **寄送記錄（CSV）**：時間、收件人、主旨、成功/失敗、錯誤訊息的總表，方便快速查閱
- **完整信件備份（ZIP）**：內含每封信的完整原始內容（`.eml` 檔），可用 Outlook、Thunderbird 等信箱軟體開啟，還原信件實際外觀

這個機制不透過 BCC 寄回自己信箱，避免每寄一封多耗用一次信箱流量與時間，備份直接下載到你的電腦上留存。

## 專案結構

```
ntu_mailer_project/
├── app.py                  # Streamlit 介面
├── mailer/
│   ├── __init__.py          # 空檔案，讓 mailer 被視為套件
│   ├── config.py             # 帳號設定資料結構
│   ├── recipients.py         # CSV 讀取、驗證、學號自動補齊網域
│   ├── template.py           # 內文變數替換
│   ├── sender.py             # SMTP 寄信邏輯
│   └── backup.py             # 寄送記錄輸出（CSV 總表 + eml 備份 ZIP）
├── docs/
│   └── tutorial.md           # 圖文教學頁面（給 GitHub Pages 使用）
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── secrets.toml.example
└── recipients_sample.csv
```

## 專案維護指南 — 想改東西該去哪裡改

| 想做的事 | 該改哪個檔案 | 說明 |
|---|---|---|
| 改介面上的文字、欄位、按鈕、版面配置 | `app.py` | 所有畫面相關的東西都在這，不涉及寄信邏輯 |
| 改帳號欄位（例如想加「寄件單位」欄位） | `mailer/config.py` | `EmailAccount` 這個資料結構定義了帳號有哪些屬性 |
| 改預設 SMTP 主機/連接埠 | `mailer/config.py` | 檔案下方 `NTU_SMTP_HOST`、`GMAIL_SMTP_HOST` 等常數 |
| 改 CSV 檢查規則、學號補齊網域邏輯 | `mailer/recipients.py` | `load_recipients()` 讀取驗證，`normalize_ntu_address()` 負責補網域 |
| 改內文變數替換規則（例如想支援 `{{name}}` 而非 `$name`） | `mailer/template.py` | `render_content()` 負責這件事 |
| 改寄信邏輯本身（例如想加已讀回條、改用其他協定） | `mailer/sender.py` | `send_one()` 寄單封，`send_batch()` 寄整批 |
| 改寄件備份的輸出格式或內容 | `mailer/backup.py` | `build_log_csv()` 產生總表，`build_eml_zip()` 打包完整信件 |
| 改圖文教學內容 | `docs/tutorial.md` | Markdown 檔案，改完 push 上去 GitHub Pages 會自動更新 |
| 改範例 CSV 內容 | `recipients_sample.csv` | 純資料檔，直接編輯即可 |
| 調整需要安裝的套件版本 | `requirements.txt` | pip 安裝清單 |

**原則：** `app.py` 只管「畫面長什麼樣、按鈕按下去呼叫誰」；`mailer/` 裡的每個檔案各自負責一件事（帳號結構、讀 CSV、換內文、寄信）。之後想加新功能，先想清楚這是「畫面的事」還是「邏輯的事」，就知道該往哪個檔案下手。

## 安全性注意事項

- 密碼絕不寫死在程式碼裡，只透過表單輸入或 `.env` 讀取
- `.env` 已加入 `.gitignore`，分享專案給其他系學會成員時不會外洩密碼
- 本工具是本機執行（localhost），密碼不會經過任何外部伺服器
- 正式寄送前務必先用「測試寄送」確認格式與內文替換正確
