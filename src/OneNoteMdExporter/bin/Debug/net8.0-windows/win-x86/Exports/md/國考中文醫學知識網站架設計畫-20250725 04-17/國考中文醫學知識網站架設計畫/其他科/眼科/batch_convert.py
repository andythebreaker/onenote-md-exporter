#!/usr/bin/env python3
"""
批量轉換所有 MHT 文件到 HTML 並分析結果
"""

import os
import sys
from pathlib import Path
import subprocess
import glob


def main():
    # 獲取當前目錄中的所有 MHT 文件
    mht_files = glob.glob("*.mht")
    
    if not mht_files:
        print("未找到 MHT 文件")
        return
    
    print(f"找到 {len(mht_files)} 個 MHT 文件:")
    for f in mht_files:
        print(f"  - {f}")
    print()
    
    # 轉換每個文件
    for mht_file in mht_files:
        print(f"轉換 {mht_file}...")
        
        try:
            # 使用最終轉換器
            cmd = [
                "python", "final_converter.py", 
                mht_file, 
                "-c", "medical_config.json", 
                "-v"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print(f"  ✓ 成功轉換")
                # 檢查輸出
                output_file = Path(mht_file).with_suffix('.final.html')
                if output_file.exists():
                    # 統計 [?] 標記的數量
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        question_marks = content.count('[?]')
                        chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
                        
                    print(f"    - 生成文件: {output_file.name}")
                    print(f"    - 丟失字符標記: {question_marks} 個")
                    print(f"    - 成功恢復中文字符: {chinese_chars} 個")
            else:
                print(f"  ✗ 轉換失敗: {result.stderr}")
                
        except Exception as e:
            print(f"  ✗ 錯誤: {e}")
        
        print()
    
    print("轉換完成!")
    
    # 顯示總結
    print("\n=== 轉換總結 ===")
    html_files = glob.glob("*.final.html")
    print(f"成功生成 {len(html_files)} 個 HTML 文件:")
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                question_marks = content.count('[?]')
                chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            
            print(f"  {html_file}: {chinese_chars} 中文字符, {question_marks} 丟失標記")
        except Exception as e:
            print(f"  {html_file}: 讀取錯誤 - {e}")


if __name__ == '__main__':
    main()
