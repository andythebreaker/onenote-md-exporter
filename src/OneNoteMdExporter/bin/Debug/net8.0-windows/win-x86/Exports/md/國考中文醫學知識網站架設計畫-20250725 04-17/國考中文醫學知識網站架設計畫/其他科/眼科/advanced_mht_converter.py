#!/usr/bin/env python3
"""
Advanced MHT to HTML Converter with Enhanced Chinese Character Support

This script provides robust conversion from MHT to HTML with special handling
for Traditional Chinese characters commonly found in medical documents.
"""

import os
import sys
import email
from email.message import Message
import quopri
import base64
import re
from pathlib import Path
from typing import Optional, Dict, Any
import argparse


class AdvancedMHTToHTMLConverter:
    """Enhanced MHT to HTML converter with better Chinese character handling."""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.default_charset = 'utf-8'
        self.verbose = False
    
    def detect_encoding(self, content: bytes) -> str:
        """Simple encoding detection for common encodings."""
        # Try common encodings in order of preference
        encodings_to_try = ['utf-8', 'utf-8-sig', 'big5', 'gb2312', 'shift_jis', 'latin1']
        
        for encoding in encodings_to_try:
            try:
                content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Default fallback
        return 'utf-8'
    
    def safe_decode_quoted_printable(self, content: str) -> str:
        """Safely decode quoted-printable content with multiple fallback strategies."""
        if self.verbose:
            print("Decoding quoted-printable content...")
        
        # Remove soft line breaks first
        content = re.sub(r'=\r?\n', '', content)
        
        # Strategy 1: Direct quoted-printable decoding
        try:
            decoded_bytes = quopri.decodestring(content.encode('latin-1'))
            # Try to detect encoding of decoded bytes
            detected_encoding = self.detect_encoding(decoded_bytes)
            return decoded_bytes.decode(detected_encoding, errors='replace')
        except Exception as e:
            if self.verbose:
                print(f"Strategy 1 failed: {e}")
        
        # Strategy 2: Manual hex decoding for quoted-printable
        try:
            # Replace =XX patterns with actual bytes
            def replace_hex(match):
                hex_val = match.group(1)
                return chr(int(hex_val, 16))
            
            # First decode =XX patterns
            decoded = re.sub(r'=([0-9A-F]{2})', replace_hex, content)
            return decoded
        except Exception as e:
            if self.verbose:
                print(f"Strategy 2 failed: {e}")
        
        # Strategy 3: Return as-is
        if self.verbose:
            print("Using content as-is")
        return content
    
    def safe_decode_base64(self, content: str) -> str:
        """Safely decode base64 content."""
        try:
            decoded_bytes = base64.b64decode(content)
            detected_encoding = self.detect_encoding(decoded_bytes)
            return decoded_bytes.decode(detected_encoding, errors='replace')
        except Exception as e:
            if self.verbose:
                print(f"Base64 decode failed: {e}")
            return content
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content from a message part with enhanced encoding handling."""
        content_type = part.get_content_type()
        
        if content_type != 'text/html':
            return None
        
        # Get charset from content type
        charset = part.get_content_charset() or self.default_charset
        self.encoding = charset
        
        if self.verbose:
            print(f"Processing part with content-type: {content_type}, charset: {charset}")
        
        # Get transfer encoding
        transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
        
        # Get the payload
        payload = part.get_payload()
        
        if transfer_encoding == 'quoted-printable':
            return self.safe_decode_quoted_printable(payload)
        elif transfer_encoding == 'base64':
            return self.safe_decode_base64(payload)
        else:
            # Handle plain content
            if isinstance(payload, bytes):
                detected_encoding = self.detect_encoding(payload)
                return payload.decode(detected_encoding, errors='replace')
            return payload
    
    def clean_and_fix_html(self, html_content: str) -> str:
        """Clean and fix HTML content with special attention to Chinese characters."""
        
        # Fix common quoted-printable artifacts
        html_content = re.sub(r'=\r?\n', '', html_content)
        
        # Fix broken HTML attributes
        html_content = re.sub(r'=3D', '=', html_content)
        html_content = re.sub(r'=22', '"', html_content)
        html_content = re.sub(r'=20', ' ', html_content)
        
        # Ensure proper HTML structure
        if not re.search(r'<!DOCTYPE|<html', html_content, re.IGNORECASE):
            html_content = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted from MHT</title>
</head>
<body>
{html_content}
</body>
</html>'''
        else:
            # Ensure UTF-8 charset is declared
            if not re.search(r'charset=.*utf-8', html_content, re.IGNORECASE):
                html_content = re.sub(
                    r'(<head[^>]*>)',
                    r'\1\n    <meta charset="utf-8">',
                    html_content,
                    flags=re.IGNORECASE
                )
        
        return html_content
    
    def convert_mht_to_html(self, mht_file_path: str, output_path: Optional[str] = None, verbose: bool = False) -> str:
        """
        Convert MHT file to HTML with enhanced Chinese character support.
        
        Args:
            mht_file_path: Path to the MHT file
            output_path: Optional output path for HTML file
            verbose: Enable verbose output
            
        Returns:
            Path to the created HTML file
        """
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read MHT file with encoding detection
        try:
            # First try to detect encoding from file
            with open(mht_path, 'rb') as f:
                raw_content = f.read()
            
            detected_encoding = self.detect_encoding(raw_content)
            if verbose:
                print(f"Detected encoding: {detected_encoding}")
            
            # Read with detected encoding
            mht_content = raw_content.decode(detected_encoding, errors='replace')
            
        except Exception as e:
            if verbose:
                print(f"Encoding detection failed: {e}")
            # Fallback to UTF-8
            with open(mht_path, 'r', encoding='utf-8', errors='replace') as f:
                mht_content = f.read()
        
        # Parse as email message
        try:
            msg = email.message_from_string(mht_content)
        except Exception as e:
            raise ValueError(f"Failed to parse MHT file: {e}")
        
        # Extract HTML content
        html_content = None
        
        if msg.is_multipart():
            for part in msg.walk():
                extracted_html = self.extract_html_from_part(part)
                if extracted_html:
                    html_content = extracted_html
                    break
        else:
            html_content = self.extract_html_from_part(msg)
        
        if not html_content:
            raise ValueError("No HTML content found in MHT file")
        
        # Clean and fix HTML
        html_content = self.clean_and_fix_html(html_content)
        
        # Determine output path
        if output_path is None:
            output_path = mht_path.with_suffix('.html')
        else:
            output_path = Path(output_path)
        
        # Write HTML file with UTF-8 BOM to ensure proper encoding
        with open(output_path, 'w', encoding='utf-8-sig', newline='\n') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Converted: {mht_path.name} -> {output_path.name}")
        
        return str(output_path)


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Advanced MHT to HTML converter with Chinese character support",
        epilog="Example: python advanced_mht_converter.py file.mht -o output.html -v"
    )
    parser.add_argument('input_path', help='MHT file or directory to convert')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--batch', action='store_true', help='Convert all MHT files in directory')
    
    args = parser.parse_args()
    
    converter = AdvancedMHTToHTMLConverter()
    input_path = Path(args.input_path)
    
    try:
        if input_path.is_file() and input_path.suffix.lower() == '.mht':
            # Convert single file
            output_file = converter.convert_mht_to_html(
                str(input_path), 
                args.output, 
                args.verbose
            )
            print(f"HTML file created: {output_file}")
            
        elif input_path.is_dir() or args.batch:
            # Convert directory
            if input_path.is_file():
                input_path = input_path.parent
            
            mht_files = list(input_path.glob('*.mht'))
            
            if not mht_files:
                print("No MHT files found in directory")
                return
            
            print(f"Found {len(mht_files)} MHT files to convert...")
            
            success_count = 0
            failed_files = []
            
            for mht_file in mht_files:
                try:
                    if args.output:
                        output_dir = Path(args.output)
                        output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = output_dir / f"{mht_file.stem}.html"
                    else:
                        output_file = None
                    
                    converter.convert_mht_to_html(str(mht_file), output_file, args.verbose)
                    success_count += 1
                    
                except Exception as e:
                    print(f"✗ Failed to convert {mht_file.name}: {e}")
                    failed_files.append(mht_file.name)
            
            print(f"\nConversion Summary:")
            print(f"Successful: {success_count}")
            print(f"Failed: {len(failed_files)}")
            
            if failed_files:
                print(f"Failed files: {', '.join(failed_files)}")
        else:
            print("Error: Input must be an MHT file or directory")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
