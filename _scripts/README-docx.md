# 產生「實作階段狀態紀錄」Word 文件

```bash
npm install docx                                   # 一次性
.venv/bin/python _scripts/verify_docx_numbers.py   # 先驗數字
node _scripts/gen_status_docx.js 90-Reports/實作階段狀態紀錄.docx
```

## ⚠️ 先驗數字，再產生

文件中的統計數字是**人工抄進 `gen_status_docx.js`** 的，不是即時查詢。
產生日期與 commit 數會自動取得，其餘不會。

這份文件的數字已經錯過三次：詞表大小、科的數量，以及一個把
「`CAS No` 欄不重複原始字串」當成「不重複 CAS 號碼」的數字
（10,008 vs 9,796 vs 10,531 是三個不同的東西）。

`verify_docx_numbers.py` 把生成器裡的每個數字對資料庫查一次，
不符就中止。**更新文件前一定要先跑它。**

資料變動後的流程：

```bash
./run_all.sh && ./run_all.sh 2026        # 重建
.venv/bin/python _scripts/verify_docx_numbers.py   # 會列出所有不符者
# 依輸出更新 gen_status_docx.js 與 verify_docx_numbers.py 的 CHECKS
node _scripts/gen_status_docx.js 90-Reports/實作階段狀態紀錄.docx
```

## 為什麼不做成即時查詢

Node 端要讀 DuckDB 得再裝一套相依套件。對一份人工閱讀的狀態快照而言，
「產生前先驗證」比「多維護一條資料管線」划算。若日後需要真正的即時同步，
應改由 Python 直接產生（Python 端本來就連著資料庫）。
