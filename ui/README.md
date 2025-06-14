# Wednesday AI Partner Web UI

這是一個現代化的 Vue.js 網頁介面，用於與 Wednesday AI Partner 進行互動。

## 功能特色

### 🗣️ 聊天介面
- 現代化的對話介面設計
- 支援即時訊息傳送
- 自動播放 TTS 語音回應
- 支援 DeepSeek R1 模型的思考過程過濾
- 響應式設計，支援手機和桌面使用

### ⚙️ 系統設定
- AI 模型選擇和配置
- TTS 語音系統設定
- RAG 資料庫管理
- 可視化的設定界面

### 🎙️ 語音功能
- 整合 GPT-SoVITS 語音合成
- 支援自動播放語音回應
- 可調整語音參數和模型路徑

## 快速開始

### 1. 安裝依賴
```bash
pip install -r ui/requirements.txt
```

### 2. 一鍵啟動
```bash
python ui/start_ui.py
```

### 3. 手動啟動
如果需要手動控制，可以分別啟動：

```bash
# 啟動 API 服務
python ui/api_server.py

# 然後在瀏覽器中開啟
# file:///path/to/your/project/ui/index.html
```

## API 端點

### 聊天對話
```
POST /chat
Content-Type: application/json

{
    "message": "你好，Wednesday",
    "use_tts": true,
    "model": "deepseek-r1:latest"
}
```

### 健康檢查
```
GET /health
```

### 音頻檔案
```
GET /audio/<filename>
```

### 重建資料庫
```
POST /rebuild-db
Content-Type: application/json

{
    "documents_path": "scripts"
}
```

## 系統需求

### 必要依賴
- Python 3.8+
- Flask 2.3+
- Vue.js 3 (透過 CDN 載入)
- 現代瀏覽器 (Chrome, Firefox, Safari, Edge)

### 硬體需求
- 記憶體: 最少 4GB，建議 8GB+
- 硬碟空間: 最少 5GB (用於模型檔案)
- 網路: 穩定的網路連線 (用於下載依賴和模型)

## 設定說明

### LLM 模型設定
- 支援多種 Ollama 模型
- 預設使用 `deepseek-r1:latest`
- 可在設定頁面切換模型

### TTS 設定
- 參考音頻路徑: 用於語音克隆的參考音頻
- GPT 模型路徑: GPT-SoVITS 的 GPT 模型檔案
- SoVITS 模型路徑: GPT-SoVITS 的 SoVITS 模型檔案

### RAG 設定
- 文檔資料夾: 存放 PDF 文檔的資料夾
- 向量資料庫路徑: ChromaDB 資料庫存放位置

## 故障排除

### 常見問題

**1. API 服務啟動失敗**
- 檢查 Python 環境和依賴是否正確安裝
- 確認端口 8000 沒有被其他程式佔用
- 查看終端錯誤訊息進行診斷

**2. TTS 語音無法播放**
- 檢查 GPT-SoVITS 模型檔案路徑
- 確認參考音頻檔案存在
- 檢查音頻檔案權限

**3. RAG 功能異常**
- 確認 scripts 資料夾中有 PDF 檔案
- 嘗試重建向量資料庫
- 檢查 Ollama 服務是否正常運行

**4. 網頁介面無法載入**
- 確認瀏覽器支援 ES6+ 語法
- 檢查網路連線 (CDN 資源)
- 使用瀏覽器開發者工具查看錯誤

### 日誌查看
- API 服務日誌會顯示在終端
- 瀏覽器控制台可查看前端錯誤
- 使用開發者工具的網路標籤監控 API 請求

## 開發說明

### 檔案結構
```
ui/
├── index.html          # 主要 HTML 檔案
├── vue_app.js          # Vue.js 應用邏輯
├── api_server.py       # Flask API 服務
├── start_ui.py         # 啟動腳本
├── requirements.txt    # Python 依賴
└── README.md          # 說明文件
```

### 自訂修改
- 樣式修改: 直接編輯 `index.html` 中的 CSS
- 功能擴展: 修改 `vue_app.js` 中的 Vue.js 代碼
- API 擴展: 修改 `api_server.py` 添加新端點

## 授權

本專案採用與主專案相同的授權條款。

## 支援

如果遇到問題，請：
1. 查看終端和瀏覽器控制台的錯誤訊息
2. 確認所有依賴和模型檔案都正確安裝
3. 查閱本 README 的故障排除章節
