# 便攜式 MHT 轉 HTML 轉換器

這個解決方案提供了一個可配置的 MHT 到 HTML 轉換器，避免了硬編碼的字符替換規則，提高了可移植性和可維護性。

## 特點

✅ **無硬編碼字符映射** - 所有字符修復規則都存在外部配置文件中
✅ **高度可配置** - 用戶可以根據需要自定義字符修復模式
✅ **保持原始編碼處理邏輯** - 專注於改進編碼解析，而不是特定字符替換
✅ **可移植性** - 代碼可以在不同項目和語言環境中重用
✅ **可維護性** - 配置與代碼分離，便於維護和更新

## 文件說明

### 核心轉換器
- `portable_mht_converter.py` - 主要的便攜式轉換器
- `mht_converter_config.json` - 字符修復配置文件（可選）

### 使用方法

#### 1. 基本轉換（無字符修復）
```bash
# 轉換單個文件
python portable_mht_converter.py input.mht

# 轉換目錄中所有文件
python portable_mht_converter.py ./directory -v
```

#### 2. 使用配置文件進行字符修復
```bash
# 創建示例配置文件
python portable_mht_converter.py --create-config

# 使用配置文件轉換
python portable_mht_converter.py input.mht -c mht_converter_config.json

# 批量轉換使用配置
python portable_mht_converter.py ./directory -c mht_converter_config.json -v
```

#### 3. 自定義輸出路徑
```bash
python portable_mht_converter.py input.mht -o output.html
python portable_mht_converter.py ./input_dir -o ./output_dir
```

## 配置文件格式

`mht_converter_config.json` 示例：

```json
{
  "restoration_patterns": {
    "���、乾眼症": "二、乾眼症",
    "���因：": "病因：",
    "診斷：���無": "診斷：並無",
    "免疫系統、內分泌等���關": "免疫系統、內分泌等相關",
    "蒸發量���高": "蒸發量過高"
  },
  "description": "Character restoration patterns for Traditional Chinese medical documents",
  "usage": "Modify the restoration_patterns to fix specific character corruption issues in your MHT files"
}
```

### 配置說明
- `restoration_patterns`: 字符修復模式的字典
  - 鍵：需要替換的損壞文本模式（支持正則表達式）
  - 值：替換後的正確文本
- 用戶可以根據自己的需求添加、修改或刪除模式

## 優勢

### 1. 可移植性
- 代碼中沒有硬編碼的特定語言字符映射
- 可以輕鬆適應不同的語言環境和用例
- 配置文件可以針對不同項目進行定制

### 2. 可維護性
- 字符修復規則與核心轉換邏輯分離
- 更新字符映射不需要修改代碼
- 配置文件可以版本控制和共享

### 3. 靈活性
- 支持正則表達式模式匹配
- 可以針對特定文檔類型創建不同的配置文件
- 可以完全禁用字符修復功能

### 4. 易用性
- 提供示例配置文件生成功能
- 清晰的命令行界面
- 詳細的錯誤處理和日誌

## 實際使用示例

### 場景1：醫學文檔轉換
```bash
# 為醫學文檔創建專用配置
python portable_mht_converter.py --create-config
# 編輯 mht_converter_config.json 添加醫學術語修復規則
# 批量轉換醫學文檔
python portable_mht_converter.py ./medical_docs -c mht_converter_config.json -o ./converted_docs
```

### 場景2：不同語言環境
```bash
# 為簡體中文創建配置文件
cp mht_converter_config.json simplified_chinese_config.json
# 編輯 simplified_chinese_config.json 適應簡體中文
# 使用簡體中文配置轉換
python portable_mht_converter.py input.mht -c simplified_chinese_config.json
```

### 場景3：純技術轉換（無字符修復）
```bash
# 不使用任何字符修復配置
python portable_mht_converter.py input.mht
# 或明確指定不使用配置
python portable_mht_converter.py input.mht -c ""
```

## 技術細節

### 編碼處理
- 自動檢測文件編碼
- 支持多種中文編碼（UTF-8、Big5、GB2312等）
- 改進的 quoted-printable 解碼
- 錯誤恢復機制

### 配置系統
- JSON 格式配置文件
- 支持正則表達式模式
- 錯誤處理和驗證
- 可選配置（沒有配置文件時仍可正常工作）

### 輸出質量
- 保持原始 HTML 結構
- 確保 UTF-8 編碼聲明
- 清理常見的編碼工件
- 最小化對原始內容的修改

## 總結

這個便攜式解決方案通過將字符修復規則外部化，解決了硬編碼的可移植性問題，同時保持了轉換質量和功能性。用戶可以根據自己的需求創建和維護配置文件，使得工具既通用又可定制。
