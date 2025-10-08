# 貢獻指南

感謝你對無線滑鼠耗電分析工具的興趣！我們歡迎各種形式的貢獻。

## 🤝 如何貢獻

### 回報問題
- 使用 [GitHub Issues](../../issues) 回報錯誤
- 請提供詳細的錯誤描述和重現步驟
- 包含你的系統環境資訊（Python版本、作業系統等）

### 建議新功能
- 在 Issues 中描述你的想法
- 說明為什麼這個功能會有用
- 如果可能，提供實作的想法

### 提交程式碼
1. Fork 這個專案
2. 建立你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟一個 Pull Request

## 📝 程式碼規範

### Python 程式碼風格
- 遵循 PEP 8 規範
- 使用有意義的變數和函數名稱
- 添加適當的註解和文檔字串
- 保持函數簡潔，單一職責

### 提交訊息格式
使用以下格式：
```
type(scope): description

[optional body]

[optional footer]
```

類型：
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文檔更新
- `style`: 程式碼格式調整
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 其他雜項

範例：
```
feat(analyzer): 新增時間區間分析功能

- 支援自定義時間範圍選擇
- 提供預設時間區間選項
- 新增區間統計比較功能
```

## 🧪 測試

在提交 Pull Request 之前，請確保：
- [ ] 程式碼能正常執行
- [ ] 新功能有適當的測試
- [ ] 所有現有測試都通過
- [ ] 文檔已更新

## 📚 開發環境設定

```bash
# 克隆專案
git clone https://github.com/your-username/mouse-power-analyzer.git
cd mouse-power-analyzer

# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝開發依賴
pip install -r requirements.txt
pip install -e .

# 執行測試
python -m pytest tests/
```

## 📄 授權

提交貢獻即表示你同意你的程式碼將在 MIT 授權下發布。