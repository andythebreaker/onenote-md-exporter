#!/usr/bin/env python3
"""
Simple usage example for MHT to HTML converter.
Converts all MHT files in the current directory to HTML.
"""

from mht_to_html_converter import MHTToHTMLConverter
from pathlib import Path
import sys


def main():
    """Convert all MHT files in current directory to HTML."""
    
    # Get current directory
    current_dir = Path('.')
    
    # Create converter instance
    converter = MHTToHTMLConverter()
    
    print("MHT to HTML Converter")
    print("=" * 40)
    print(f"Working directory: {current_dir.absolute()}")
    
    # Find all MHT files
    mht_files = list(current_dir.glob('*.mht'))
    
    if not mht_files:
        print("No MHT files found in current directory.")
        return
    
    print(f"\nFound {len(mht_files)} MHT files:")
    for mht_file in mht_files:
        print(f"  - {mht_file.name}")
    
    print("\nStarting conversion...")
    
    # Convert each file
    successful = 0
    failed = 0
    
    for mht_file in mht_files:
        try:
            html_file = converter.convert_mht_to_html(str(mht_file))
            print(f"✓ {mht_file.name} -> {Path(html_file).name}")
            successful += 1
        except Exception as e:
            print(f"✗ Failed to convert {mht_file.name}: {e}")
            failed += 1
    
    print(f"\nConversion complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    # Check one of the converted files for Chinese characters
    if successful > 0:
        html_files = list(current_dir.glob('*.html'))
        if html_files:
            print(f"\nChecking Chinese character preservation in {html_files[0].name}...")
            try:
                with open(html_files[0], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for Chinese characters
                chinese_chars = []
                for char in content:
                    if '\u4e00' <= char <= '\u9fff':  # CJK Unified Ideographs
                        if char not in chinese_chars and len(chinese_chars) < 20:
                            chinese_chars.append(char)
                
                if chinese_chars:
                    print(f"✓ Chinese characters found: {''.join(chinese_chars[:10])}{'...' if len(chinese_chars) > 10 else ''}")
                else:
                    print("No Chinese characters detected (file may be in English)")
                    
            except Exception as e:
                print(f"Warning: Could not check Chinese characters: {e}")


if __name__ == '__main__':
    main()
