# MHT to HTML Converter with Chinese Character Support

A Python utility for converting MHT (MIME HTML) files to clean HTML files while preserving Traditional Chinese (zh-tw) characters. This tool is specifically designed to handle medical documents and other content with Chinese text.

## Features

- ✅ **Chinese Character Preservation**: Maintains Traditional Chinese characters during conversion
- ✅ **Multiple Encoding Support**: Handles UTF-8, Big5, GB2312, and other encodings
- ✅ **Quoted-Printable Decoding**: Properly decodes MHT content encoding
- ✅ **Batch Processing**: Convert multiple files at once
- ✅ **Error Handling**: Robust error handling with fallback strategies
- ✅ **Medical Document Support**: Optimized for medical terminology and documents

## Files Included

### Core Converter
- `mht_to_html_converter.py` - Main converter class with comprehensive MHT to HTML conversion
- `advanced_mht_converter.py` - Enhanced version with additional encoding detection

### Utilities and Examples
- `convert_all.py` - Simple script to convert all MHT files in current directory
- `test_conversion.py` - Test script to verify Chinese character preservation
- `demo.py` - Comprehensive demonstration and validation script

## Quick Start

### Method 1: Command Line Usage

```bash
# Convert a single file
python mht_to_html_converter.py input.mht

# Convert with custom output
python mht_to_html_converter.py input.mht -o output.html

# Convert all MHT files in directory
python mht_to_html_converter.py . -o output_directory
```

### Method 2: Python Script Usage

```python
from mht_to_html_converter import MHTToHTMLConverter

# Create converter instance
converter = MHTToHTMLConverter()

# Convert single file
html_file = converter.convert_mht_to_html('input.mht')
print(f"Converted to: {html_file}")

# Convert directory
converter.convert_directory('.', 'output')
```

### Method 3: Batch Convert Current Directory

```bash
python convert_all.py
```

## Detailed Usage Examples

### Example 1: Converting Medical Documents

```python
from mht_to_html_converter import MHTToHTMLConverter

converter = MHTToHTMLConverter()

# Medical document files with Chinese characters
medical_files = ['淚液系統.mht', '眼瞼.mht', '結膜.mht']

for mht_file in medical_files:
    try:
        html_file = converter.convert_mht_to_html(mht_file)
        print(f"✓ Successfully converted: {mht_file} -> {html_file}")
    except Exception as e:
        print(f"✗ Failed to convert {mht_file}: {e}")
```

### Example 2: Validating Chinese Character Preservation

```python
# Run the test script
python test_conversion.py

# Or use the demo script
python demo.py
```

## Command Line Options

```bash
python mht_to_html_converter.py [-h] [-o OUTPUT] [--encoding ENCODING] input_path

positional arguments:
  input_path            Path to MHT file or directory containing MHT files

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output path for HTML file(s)
  --encoding ENCODING   Text encoding to use (default: utf-8)
```

## Technical Details

### Supported Input Formats
- MHT (MIME HTML) files created by Microsoft OneNote, Word, or other applications
- Files with Traditional Chinese, Simplified Chinese, or mixed content
- Files using various encodings (UTF-8, Big5, GB2312, etc.)

### Character Encoding Handling
1. **Automatic Detection**: Attempts to detect file encoding
2. **Quoted-Printable Decoding**: Handles MHT's quoted-printable content encoding
3. **Fallback Strategies**: Multiple fallback methods for difficult encodings
4. **UTF-8 Output**: Always outputs clean UTF-8 encoded HTML

### Chinese Character Support
- Traditional Chinese (繁體中文) - Primary focus
- Simplified Chinese (简体中文) - Also supported
- Medical terminology preservation
- Proper font family declarations for Chinese text

## Troubleshooting

### Common Issues and Solutions

**Issue**: Chinese characters appear as question marks (?)
**Solution**: The original MHT file may have encoding issues. Try the advanced converter:
```bash
python advanced_mht_converter.py input.mht --verbose
```

**Issue**: Some characters show as replacement characters (�)
**Solution**: This indicates encoding conflicts in the original file. The converter preserves as much content as possible.

**Issue**: HTML structure is malformed
**Solution**: The converter automatically adds proper HTML structure and UTF-8 declarations.

### Validation

Use the test script to validate conversion quality:
```bash
python test_conversion.py
```

This will:
- Check for proper UTF-8 encoding declaration
- Verify Chinese character preservation
- Detect potential encoding issues
- Validate HTML structure

## Performance

### Conversion Stats (Example)
- `淚液系統.mht` (2.3 MB) → `淚液系統.html` (56 KB) - 1,278 Chinese characters preserved
- `眼瞼.mht` (2.2 MB) → `眼瞼.html` (58 KB) - 1,352 Chinese characters preserved  
- `結膜.mht` (186 KB) → `結膜.html` (176 KB) - 4,465 Chinese characters preserved

### Typical Conversion Times
- Small files (<1 MB): < 1 second
- Medium files (1-5 MB): 1-3 seconds
- Large files (>5 MB): 3-10 seconds

## Requirements

- Python 3.6 or higher
- Standard library modules only (no external dependencies)

## License

This script is provided as-is for educational and utility purposes. Feel free to modify and distribute according to your needs.

## Contributing

To improve Chinese character handling:
1. Test with various MHT files
2. Report encoding issues
3. Suggest improvements for specific character sets
4. Add support for additional medical terminologies

---

**Note**: This converter is optimized for Traditional Chinese medical documents but works well with any MHT files containing Chinese characters.
