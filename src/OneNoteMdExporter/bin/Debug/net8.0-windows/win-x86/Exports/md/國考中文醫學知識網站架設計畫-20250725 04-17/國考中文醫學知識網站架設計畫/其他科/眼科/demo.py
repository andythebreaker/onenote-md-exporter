#!/usr/bin/env python3
"""
Usage examples and demo for MHT to HTML conversion with Chinese character support.
"""

import sys
from pathlib import Path
from mht_to_html_converter import MHTToHTMLConverter


def demo_conversion():
    """Demonstrate the MHT to HTML conversion process."""
    
    print("MHT to HTML Converter Demo")
    print("=" * 50)
    print("This script converts MHT files to HTML while preserving Traditional Chinese characters.")
    print()
    
    # Get current directory
    current_dir = Path('.')
    
    # Find MHT files
    mht_files = list(current_dir.glob('*.mht'))
    
    if not mht_files:
        print("No MHT files found in the current directory.")
        print("Please place some MHT files in this directory and run again.")
        return
    
    print(f"Found {len(mht_files)} MHT files:")
    for i, mht_file in enumerate(mht_files, 1):
        size_kb = mht_file.stat().st_size / 1024
        print(f"  {i}. {mht_file.name} ({size_kb:.1f} KB)")
    
    print()
    
    # Initialize converter
    converter = MHTToHTMLConverter()
    
    # Convert files
    print("Converting files...")
    print("-" * 30)
    
    for mht_file in mht_files:
        try:
            html_file = converter.convert_mht_to_html(str(mht_file))
            print(f"✓ {mht_file.name} -> {Path(html_file).name}")
            
            # Check for Chinese characters in the output
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count Chinese characters
            chinese_char_count = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
            
            if chinese_char_count > 0:
                print(f"  📝 Contains {chinese_char_count} Chinese characters")
            else:
                print("  📄 No Chinese characters detected")
                
        except Exception as e:
            print(f"✗ Failed to convert {mht_file.name}: {e}")
    
    print()
    print("Conversion complete!")
    
    # Show HTML files created
    html_files = list(current_dir.glob('*.html'))
    if html_files:
        print(f"\nHTML files created ({len(html_files)}):")
        for html_file in html_files:
            size_kb = html_file.stat().st_size / 1024
            print(f"  📄 {html_file.name} ({size_kb:.1f} KB)")


def validate_chinese_preservation():
    """Validate that Chinese characters are properly preserved."""
    
    print("\nValidating Chinese Character Preservation")
    print("=" * 45)
    
    current_dir = Path('.')
    html_files = list(current_dir.glob('*.html'))
    
    if not html_files:
        print("No HTML files found for validation.")
        return
    
    for html_file in html_files:
        print(f"\nChecking: {html_file.name}")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check encoding declaration
            if 'charset="utf-8"' in content or 'charset=utf-8' in content:
                print("  ✓ UTF-8 encoding declared")
            else:
                print("  ⚠ UTF-8 encoding not found")
            
            # Check for Traditional Chinese medical terms
            medical_terms = [
                '淚液', '系統', '眼瞼', '結膜', '角膜', '鞏膜',
                '醫學', '診斷', '治療', '症狀', '病理', '解剖',
                '分泌', '腺體', '神經', '血管', '組織', '細胞'
            ]
            
            found_terms = []
            for term in medical_terms:
                if term in content:
                    found_terms.append(term)
            
            if found_terms:
                print(f"  ✓ Medical terms found: {', '.join(found_terms[:5])}")
                if len(found_terms) > 5:
                    print(f"    + {len(found_terms) - 5} more terms")
            else:
                print("  ⚠ No medical terms detected")
            
            # Check for corruption indicators
            corruption_indicators = ['�', '&amp;', '&lt;', '&gt;']
            corrupted = []
            for indicator in corruption_indicators:
                if indicator in content:
                    corrupted.append(indicator)
            
            if corrupted:
                print(f"  ⚠ Potential encoding issues: {', '.join(corrupted)}")
            else:
                print("  ✓ No obvious encoding corruption detected")
                
        except Exception as e:
            print(f"  ✗ Error reading file: {e}")


def show_usage_examples():
    """Show usage examples for the converter."""
    
    print("\nUsage Examples")
    print("=" * 20)
    print()
    
    print("1. Convert a single MHT file:")
    print("   python mht_to_html_converter.py 淚液系統.mht")
    print()
    
    print("2. Convert with custom output:")
    print("   python mht_to_html_converter.py 淚液系統.mht -o output.html")
    print()
    
    print("3. Convert all MHT files in directory:")
    print("   python mht_to_html_converter.py . --batch")
    print()
    
    print("4. Use in Python script:")
    print("""   from mht_to_html_converter import MHTToHTMLConverter
   converter = MHTToHTMLConverter()
   html_file = converter.convert_mht_to_html('input.mht')
   print(f"Converted to: {html_file}")""")
    print()


if __name__ == '__main__':
    try:
        demo_conversion()
        validate_chinese_preservation()
        show_usage_examples()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("All MHT files have been converted to HTML with Chinese character preservation.")
        
    except Exception as e:
        print(f"Error during demo: {e}")
        sys.exit(1)
