#!/usr/bin/env python3
"""
MHT to HTML Converter with Traditional Chinese (zh-tw) Character Support

This script converts MHT (MIME HTML) files to clean HTML files while preserving
Traditional Chinese characters and proper encoding.
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


class MHTToHTMLConverter:
    """Convert MHT files to HTML while preserving Chinese characters."""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.default_charset = 'utf-8'
    
    def decode_quoted_printable(self, content: str) -> str:
        """Decode quoted-printable content with improved multi-byte character handling."""
        try:
            # Remove soft line breaks (=\n)
            content = re.sub(r'=\r?\n', '', content)
            
            # Strategy 1: Improved hex sequence decoding for multi-byte characters
            def decode_hex_sequence(match):
                """Decode a sequence of =XX hex codes as UTF-8 bytes."""
                hex_codes = re.findall(r'=([0-9A-F]{2})', match.group(0))
                try:
                    # Convert hex codes to bytes
                    byte_data = bytes([int(code, 16) for code in hex_codes])
                    # Try to decode as UTF-8
                    return byte_data.decode('utf-8', errors='replace')
                except (ValueError, UnicodeDecodeError):
                    # If decoding fails, return the original sequence
                    return match.group(0)
            
            # Look for sequences of quoted-printable hex codes (common for multi-byte chars)
            # Pattern matches sequences like =E6=B7=9A (3-byte UTF-8 sequence)
            hex_sequence_pattern = r'(?:=[8-9A-F][0-9A-F]){1,4}'
            content = re.sub(hex_sequence_pattern, decode_hex_sequence, content)
            
            # Strategy 2: Standard quoted-printable decoding for remaining content
            try:
                # Encode as latin-1 for quopri processing
                encoded_content = content.encode('latin-1', errors='ignore')
                decoded_bytes = quopri.decodestring(encoded_content)
                
                # Try multiple encodings to decode the result
                for encoding in ['utf-8', 'big5', 'gb2312', 'shift_jis']:
                    try:
                        return decoded_bytes.decode(encoding, errors='strict')
                    except UnicodeDecodeError:
                        continue
                
                # Fallback with error replacement
                return decoded_bytes.decode('utf-8', errors='replace')
                
            except Exception:
                # If all else fails, return the processed content
                return content
                
        except Exception as e:
            print(f"Warning: Error decoding quoted-printable: {e}")
            return content
    
    def decode_base64(self, content: str) -> str:
        """Decode base64 content safely."""
        try:
            decoded_bytes = base64.b64decode(content)
            return decoded_bytes.decode(self.encoding, errors='replace')
        except Exception as e:
            print(f"Warning: Error decoding base64: {e}")
            return content
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content from a message part."""
        content_type = part.get_content_type()
        
        if content_type != 'text/html':
            return None
        
        # Get charset from content type
        charset = part.get_content_charset() or self.default_charset
        self.encoding = charset
        
        # Get transfer encoding
        transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
        
        # Get the payload
        payload = part.get_payload()
        
        if transfer_encoding == 'quoted-printable':
            return self.decode_quoted_printable(payload)
        elif transfer_encoding == 'base64':
            return self.decode_base64(payload)
        else:
            # Try to decode as string
            if isinstance(payload, bytes):
                return payload.decode(self.encoding, errors='replace')
            return payload
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean and format HTML content with generic encoding fixes."""
        # Fix common encoding issues with quoted-printable
        html_content = re.sub(r'=\r?\n', '', html_content)
        
        # Fix broken HTML attributes from quoted-printable encoding
        html_content = re.sub(r'=([0-9A-F]{2})', lambda m: chr(int(m.group(1), 16)), html_content)
        
        # Generic post-processing for common HTML encoding issues
        html_content = self.fix_common_encoding_artifacts(html_content)
        
        # Ensure proper DOCTYPE and HTML structure
        if not html_content.strip().startswith('<!DOCTYPE') and not html_content.strip().startswith('<html'):
            html_content = f'<!DOCTYPE html>\n<html lang="zh-TW">\n<head>\n<meta charset="utf-8">\n</head>\n<body>\n{html_content}\n</body>\n</html>'
        
        # Ensure UTF-8 charset is specified
        if '<meta charset=' not in html_content and '<meta http-equiv=' not in html_content:
            html_content = re.sub(
                r'(<head[^>]*>)',
                r'\1\n<meta charset="utf-8">',
                html_content,
                flags=re.IGNORECASE
            )
        
        return html_content
    
    def fix_common_encoding_artifacts(self, content: str) -> str:
        """Fix common encoding artifacts without hardcoded character replacements."""
        
        # Fix HTML entity encoding issues
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&nbsp;': ' '
        }
        
        for entity, char in html_entities.items():
            content = content.replace(entity, char)
        
        # Fix double-encoded UTF-8 sequences (common issue)
        # This attempts to detect and fix double-encoding without hardcoded mappings
        try:
            # Look for potential double-encoded UTF-8 patterns
            # This is a generic approach that tries to detect and fix encoding issues
            encoded_bytes = content.encode('latin-1', errors='ignore')
            
            # Try to decode as UTF-8 to see if it was double-encoded
            try:
                potential_fix = encoded_bytes.decode('utf-8', errors='strict')
                # Only use the fix if it results in fewer replacement characters
                if content.count('�') > potential_fix.count('�'):
                    content = potential_fix
            except UnicodeDecodeError:
                pass  # Keep original content
                
        except Exception:
            pass  # Keep original content if any processing fails
        
        return content
    
    def convert_mht_to_html(self, mht_file_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert MHT file to HTML.
        
        Args:
            mht_file_path: Path to the MHT file
            output_path: Optional output path for HTML file
            
        Returns:
            Path to the created HTML file
        """
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        # Read MHT file with proper encoding detection
        try:
            # Try UTF-8 first
            with open(mht_path, 'r', encoding='utf-8', errors='replace') as f:
                mht_content = f.read()
        except UnicodeDecodeError:
            # Fallback to other encodings
            for encoding in ['utf-8-sig', 'big5', 'gb2312', 'latin1']:
                try:
                    with open(mht_path, 'r', encoding=encoding, errors='replace') as f:
                        mht_content = f.read()
                    print(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode MHT file with any supported encoding")
        
        # Parse as email message
        try:
            msg = email.message_from_string(mht_content)
        except Exception as e:
            raise ValueError(f"Failed to parse MHT file as email message: {e}")
        
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
        
        # Clean and format HTML
        html_content = self.clean_html_content(html_content)
        
        # Determine output path
        if output_path is None:
            output_path = mht_path.with_suffix('.html')
        else:
            output_path = Path(output_path)
        
        # Write HTML file with UTF-8 encoding
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(html_content)
        
        print(f"Successfully converted: {mht_path.name} -> {output_path.name}")
        return str(output_path)
    
    def convert_directory(self, directory_path: str, output_dir: Optional[str] = None):
        """Convert all MHT files in a directory."""
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = dir_path
        
        mht_files = list(dir_path.glob('*.mht'))
        
        if not mht_files:
            print("No MHT files found in the directory")
            return
        
        print(f"Found {len(mht_files)} MHT files to convert...")
        
        successful_conversions = 0
        failed_conversions = []
        
        for mht_file in mht_files:
            try:
                output_file = output_path / f"{mht_file.stem}.html"
                self.convert_mht_to_html(str(mht_file), str(output_file))
                successful_conversions += 1
            except Exception as e:
                print(f"Failed to convert {mht_file.name}: {e}")
                failed_conversions.append(mht_file.name)
        
        print(f"\nConversion complete!")
        print(f"Successful: {successful_conversions}")
        print(f"Failed: {len(failed_conversions)}")
        
        if failed_conversions:
            print("Failed files:", ", ".join(failed_conversions))


def main():
    """Main function to run the converter."""
    parser = argparse.ArgumentParser(
        description="Convert MHT files to HTML with Traditional Chinese character support"
    )
    parser.add_argument(
        'input_path',
        help='Path to MHT file or directory containing MHT files'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output path for HTML file(s). If not specified, creates HTML files in the same directory'
    )
    parser.add_argument(
        '--encoding',
        default='utf-8',
        help='Text encoding to use (default: utf-8)'
    )
    
    args = parser.parse_args()
    
    converter = MHTToHTMLConverter()
    converter.encoding = args.encoding
    
    input_path = Path(args.input_path)
    
    try:
        if input_path.is_file() and input_path.suffix.lower() == '.mht':
            # Convert single file
            output_file = converter.convert_mht_to_html(str(input_path), args.output)
            print(f"HTML file created: {output_file}")
        elif input_path.is_dir():
            # Convert directory
            converter.convert_directory(str(input_path), args.output)
        else:
            print("Error: Input path must be an MHT file or directory containing MHT files")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
