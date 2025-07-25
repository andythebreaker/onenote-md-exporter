#!/usr/bin/env python3
"""
Test script to verify Chinese character preservation in MHT to HTML conversion.
"""

import os
import sys
from pathlib import Path
from mht_to_html_converter import MHTToHTMLConverter


def test_chinese_character_preservation():
    """Test that Traditional Chinese characters are preserved during conversion."""
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    # Find MHT files in current directory
    mht_files = list(current_dir.glob('*.mht'))
    
    if not mht_files:
        print("No MHT files found for testing")
        return
    
    print(f"Testing Chinese character preservation with {len(mht_files)} files...")
    
    converter = MHTToHTMLConverter()
    
    for mht_file in mht_files:
        print(f"\nTesting: {mht_file.name}")
        
        try:
            # Convert MHT to HTML
            html_file = converter.convert_mht_to_html(str(mht_file))
            
            # Read the generated HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Check for common Traditional Chinese characters in medical context
            chinese_chars_found = []
            test_chars = [
                '淚液', '系統', '眼瞼', '結膜',  # From filenames
                '醫學', '知識', '網站',  # From directory path
                '中文', '繁體', '正體'   # General Traditional Chinese indicators
            ]
            
            for char_group in test_chars:
                if char_group in html_content:
                    chinese_chars_found.append(char_group)
            
            if chinese_chars_found:
                print(f"✓ Chinese characters preserved: {', '.join(chinese_chars_found)}")
            else:
                print("⚠ No test Chinese characters found (may still be valid)")
            
            # Check encoding declaration
            if 'charset="utf-8"' in html_content or 'charset=utf-8' in html_content:
                print("✓ UTF-8 encoding properly declared")
            else:
                print("⚠ UTF-8 encoding not found in HTML")
            
            # Check for proper HTML structure
            if '<html' in html_content and '</html>' in html_content:
                print("✓ Valid HTML structure")
            else:
                print("⚠ HTML structure may be incomplete")
                
        except Exception as e:
            print(f"✗ Error converting {mht_file.name}: {e}")


def show_file_info():
    """Show information about the files in the current directory."""
    current_dir = Path(__file__).parent
    
    print("Files in current directory:")
    print("=" * 50)
    
    for file_path in sorted(current_dir.iterdir()):
        if file_path.is_file():
            try:
                size = file_path.stat().st_size
                print(f"{file_path.name:<30} ({size:,} bytes)")
            except:
                print(f"{file_path.name:<30} (size unknown)")


if __name__ == '__main__':
    print("MHT to HTML Converter - Chinese Character Test")
    print("=" * 50)
    
    show_file_info()
    print()
    test_chinese_character_preservation()
