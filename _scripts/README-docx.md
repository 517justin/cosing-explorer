# 產生「實作階段狀態紀錄」Word 文件

```bash
npm install docx          # 一次性，docx 為 npm 套件
node _scripts/gen_status_docx.js 90-Reports/實作階段狀態紀錄.docx
```

文件中的數字**不是**自動查詢資料庫得來的，是產生當下由
`_scripts/00_profile.py`／`04_clean_taxon.py` 的輸出人工填入 `gen_status_docx.js`。
資料變動後重跑本腳本前，請先確認腳本內的數字仍與 `kb.duckdb` 一致：

```bash
./run_all.sh              # 重建資料庫並印出最新數字
```
