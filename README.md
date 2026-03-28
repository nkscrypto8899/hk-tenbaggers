# 🐵 港股十倍股量化選股系統

根據 24 年研究 464 間「十倍股」得出嘅 6 個核心準則，專為香港小型股票優化。

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hk-tenbaggers.streamlit.app)

## 🌐 立即使用

👉 **https://hk-tenbaggers.streamlit.app**

## 📋 與美股版分別

| 項目 | 美股版 | 港股版 |
|------|--------|--------|
| 市值上限 | $2.5 億美元 | **HK$5 億** |
| 默認貨幣 | 美元 | 港幣 |
| 默認股票 | 美國小型股 | **香港小型股** |
| 主題顏色 | 橙色 | **紅色（港交所色）** |

## 📋 6 個選股準則

| # | 準則 | 說明 |
|---|------|------|
| 1 | 初始市值要細 | 市值 < HK$5 億 |
| 2 | 高價值 + 高獲利 | Book-to-Market 高、ROA 高、EBITDA 高 |
| 3 | 強勁現金流 | FCF Yield 高 |
| 4 | 低位入場 | 股價接近 12 個月低位 |
| 5 | 資產/盈餘平衡 | 資產增速 < 盈餘增速 |
| 6 | 利率敏感度 | Beta 值高 |

## 🚀 部署到 Streamlit Cloud（免費）

### 方式一：Fork + 一鍵部署

1. Fork 呢個 Repo
2. 去 [streamlit.io/cloud](https://streamlit.io/cloud) 
3. 選擇你嘅 GitHub Repo
4. Branch 選 `main`
5. Main file path 填 `app.py`
6. 點擊 **Deploy!**

### 方式二：本地運行

```bash
# Clone Repo
git clone https://github.com/YOUR_USERNAME/hk-tenbaggers.git
cd hk-tenbaggers

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安裝依賴
pip install -r requirements.txt

# 運行
streamlit run app.py
```

## 📁 專案結構

```
hk-tenbaggers/
├── app.py              # Streamlit Web App (主程序)
├── scoring_engine.py   # 評分引擎
├── settings.py        # 配置讀取
├── settings.yaml      # 設定檔 (港幣)
├── requirements.txt   # 依賴列表
├── .streamlit/        # Streamlit 配置
│   └── config.toml
└── README.md
```

## 🎯 評分機制

```
總分 = Σ (各項分數 × 權重)

各項分數 0-100，越高越好
總分 70+ = 🔥 強烈建議關注
總分 55+ = 👍 具備潛質
總分 40+ = ⚠️ 一般
總分 <40 = ❌ 不符合標準
```

## ⚠️ 風險提示

1. **過去表現唔等於未來** - 十倍股係統計規律，唔擔保未來表現
2. **數據延遲** - Yahoo Finance 免費數據可能有延遲
3. **忽略主觀因素** - 系統唔考慮管理層、行業趨勢等
4. **需要配合分析** - 量化篩選係開始，唔係終點

## 📚 參考資料

- Greenblat, M. (2006) - "How the Small Cap Anomaly and the Net Net Strategy Can Combine into a 10-Bagger System"
- 學術研究：過去 24 年 464 間倍升股嘅共同特質分析

## 📜 License

MIT License

---

*Developed by Ape 仔 🐵*
