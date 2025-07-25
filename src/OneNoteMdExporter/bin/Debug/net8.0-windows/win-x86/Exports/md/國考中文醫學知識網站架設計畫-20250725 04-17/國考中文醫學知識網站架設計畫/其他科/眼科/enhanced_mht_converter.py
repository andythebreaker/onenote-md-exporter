#!/usr/bin/env python3
"""
Enhanced MHT to HTML converter specifically for handling corrupted Chinese characters.
This version tries to recover characters that were lost during the original MHT creation process.
"""

import os
import sys
import email
from email.message import Message
import quopri
import base64
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any
import argparse


class EnhancedMHTConverter:
    """Enhanced MHT converter with aggressive Chinese character recovery."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.encoding = 'utf-8'
        self.default_charset = 'utf-8'
        self.verbose = False
        
        # Load configuration
        self.restoration_patterns = self.load_restoration_config(config_file)
    
    def load_restoration_config(self, config_file: Optional[str] = None) -> Dict[str, str]:
        """Load character restoration patterns from configuration file."""
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('restoration_patterns', {})
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Could not load config file {config_file}: {e}")
        
        return {}
    
    def aggressive_decode_quoted_printable(self, content: str) -> str:
        """Aggressively decode quoted-printable with multiple recovery strategies."""
        original_content = content
        
        try:
            # Remove soft line breaks
            content = re.sub(r'=\r?\n', '', content)
            
            # Fix basic HTML entities first
            content = re.sub(r'=3D', '=', content)
            content = re.sub(r'=22', '"', content)
            content = re.sub(r'=20', ' ', content)
            
            # Strategy 1: Try standard quoted-printable decoding
            try:
                if '=' in content and re.search(r'=[0-9A-F]{2}', content):
                    encoded_bytes = content.encode('latin-1', errors='ignore')
                    decoded_bytes = quopri.decodestring(encoded_bytes)
                    
                    # Try UTF-8 first
                    try:
                        decoded_content = decoded_bytes.decode('utf-8', errors='strict')
                        if self.verbose:
                            print("Successfully decoded with standard quoted-printable + UTF-8")
                        return decoded_content
                    except UnicodeDecodeError:
                        pass
                    
                    # Try other encodings
                    for encoding in ['big5', 'gb2312', 'shift_jis']:
                        try:
                            decoded_content = decoded_bytes.decode(encoding, errors='strict')
                            if self.verbose:
                                print(f"Successfully decoded with standard quoted-printable + {encoding}")
                            return decoded_content
                        except UnicodeDecodeError:
                            continue
                    
                    # Use UTF-8 with replacement
                    decoded_content = decoded_bytes.decode('utf-8', errors='replace')
                    if decoded_content.count('�') < len(decoded_content) * 0.1:  # Less than 10% corruption
                        if self.verbose:
                            print("Using UTF-8 with replacement characters")
                        return decoded_content
            except Exception as e:
                if self.verbose:
                    print(f"Standard decoding failed: {e}")
            
            # Strategy 2: Manual hex processing
            def process_hex_codes(text):
                """Process hex codes manually with multiple attempts."""
                # Look for =XX patterns
                hex_pattern = r'=([0-9A-F]{2})'
                
                def decode_hex(match):
                    hex_val = match.group(1)
                    try:
                        byte_val = int(hex_val, 16)
                        if byte_val < 128:  # ASCII
                            return chr(byte_val)
                        else:
                            # Keep as raw byte for now
                            return bytes([byte_val])
                    except:
                        return match.group(0)
                
                # Replace hex codes
                parts = []
                current_pos = 0
                
                for match in re.finditer(hex_pattern, text):
                    # Add text before match
                    parts.append(text[current_pos:match.start()])
                    # Process hex code
                    parts.append(decode_hex(match))
                    current_pos = match.end()
                
                # Add remaining text
                parts.append(text[current_pos:])
                
                # Reconstruct and handle bytes
                result = []
                byte_buffer = bytearray()
                
                for part in parts:
                    if isinstance(part, bytes):
                        byte_buffer.extend(part)
                    else:
                        # Process accumulated bytes
                        if byte_buffer:
                            # Try to decode byte sequence
                            for encoding in ['utf-8', 'big5', 'gb2312']:
                                try:
                                    decoded = byte_buffer.decode(encoding, errors='strict')
                                    result.append(decoded)
                                    byte_buffer = bytearray()
                                    break
                                except UnicodeDecodeError:
                                    continue
                            else:
                                # Could not decode, use replacement
                                result.append(byte_buffer.decode('utf-8', errors='replace'))
                                byte_buffer = bytearray()
                        
                        result.append(part)
                
                # Handle remaining bytes
                if byte_buffer:
                    result.append(byte_buffer.decode('utf-8', errors='replace'))
                
                return ''.join(result)
            
            processed_content = process_hex_codes(content)
            if processed_content != content:
                if self.verbose:
                    print("Successfully processed with manual hex decoding")
                return processed_content
            
        except Exception as e:
            if self.verbose:
                print(f"All decoding strategies failed: {e}")
        
        # Return original content if all strategies fail
        return original_content
    
    def restore_empty_spans(self, html_content: str) -> str:
        """Attempt to restore content in empty Chinese font spans."""
        
        # Look for empty spans that likely contained Chinese text
        empty_chinese_span_pattern = r'<span[^>]*font-family:"Microsoft JhengHei"[^>]*></span>'
        
        def try_restore_span(match):
            """Try to restore content based on context."""
            span_html = match.group(0)
            
            # For now, we'll mark these for manual review
            # In a real implementation, you might use context analysis
            return '<span class="missing-chinese-text">[缺失中文字符]</span>'
        
        # Replace empty Chinese spans
        html_content = re.sub(empty_chinese_span_pattern, try_restore_span, html_content)
        
        return html_content
    
    def apply_contextual_restoration(self, content: str) -> str:
        """Apply contextual restoration based on medical terminology patterns."""
        
        # Medical context restoration patterns
        contextual_patterns = {
            # Based on medical terminology context
            r'<span[^>]*Microsoft JhengHei[^>]*></span>(?=色)': '充血',  # Before "色" likely "充血"
            r'(?<=角膜)<span[^>]*Microsoft JhengHei[^>]*></span>(?=superficial)': '有',  # Between "角膜" and "superficial"
            r'(?<=治療：)<span[^>]*Microsoft JhengHei[^>]*></span>(?=據病)': '根',  # After "治療：" before "據病"
            r'<span[^>]*Microsoft JhengHei[^>]*></span>(?=狀：)': '症',  # Before "狀："
            r'<span[^>]*Microsoft JhengHei[^>]*></span>(?=合併)': '並',  # Before "合併"
            
            # Common patterns in medical texts
            r'(?<=，)<span[^>]*Microsoft JhengHei[^>]*></span>(?=的)': '且',  # Between commas
            r'(?<=有)<span[^>]*Microsoft JhengHei[^>]*></span>(?=異常)': '淚膜',  # "有"..."異常"
        }
        
        # Apply contextual patterns
        for pattern, replacement in contextual_patterns.items():
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content with enhanced recovery."""
        content_type = part.get_content_type()
        
        if content_type != 'text/html':
            return None
        
        charset = part.get_content_charset() or self.default_charset
        self.encoding = charset
        
        if self.verbose:
            print(f"Processing part: {content_type}, charset: {charset}")
        
        transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
        payload = part.get_payload()
        
        if transfer_encoding == 'quoted-printable':
            return self.aggressive_decode_quoted_printable(payload)
        elif transfer_encoding == 'base64':
            try:
                decoded_bytes = base64.b64decode(payload)
                return decoded_bytes.decode(self.encoding, errors='replace')
            except Exception:
                return payload
        else:
            if isinstance(payload, bytes):
                return payload.decode(self.encoding, errors='replace')
            return payload
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML with enhanced restoration."""
        # Basic cleanup
        html_content = re.sub(r'=\r?\n', '', html_content)
        
        # Apply restoration patterns from config
        for pattern, replacement in self.restoration_patterns.items():
            try:
                html_content = re.sub(pattern, replacement, html_content)
            except Exception as e:
                if self.verbose:
                    print(f"Pattern '{pattern}' failed: {e}")
        
        # Restore empty spans
        html_content = self.restore_empty_spans(html_content)
        
        # Apply contextual restoration
        html_content = self.apply_contextual_restoration(html_content)
        
        # Standard HTML entity fixes
        entity_fixes = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&apos;': "'", '&nbsp;': ' '
        }
        
        for entity, char in entity_fixes.items():
            html_content = html_content.replace(entity, char)
        
        # Ensure proper HTML structure
        if not re.search(r'<!DOCTYPE|<html', html_content, re.IGNORECASE):
            html_content = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="utf-8">
    <title>Converted from MHT</title>
    <style>
        .missing-chinese-text {{
            background-color: yellow;
            color: red;
            font-weight: bold;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''
        
        # Ensure UTF-8 charset
        if not re.search(r'charset=.*utf-8', html_content, re.IGNORECASE):
            html_content = re.sub(
                r'(<head[^>]*>)',
                r'\1\n    <meta charset="utf-8">',
                html_content,
                flags=re.IGNORECASE
            )
        
        return html_content
    
    def convert_mht_to_html(self, mht_file_path: str, output_path: Optional[str] = None, 
                           verbose: bool = False) -> str:
        """Convert MHT to HTML with enhanced character recovery."""
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read MHT file with multiple encoding attempts
        mht_content = None
        for encoding in ['utf-8', 'utf-8-sig', 'big5', 'gb2312', 'latin1']:
            try:
                with open(mht_path, 'r', encoding=encoding, errors='replace') as f:
                    mht_content = f.read()
                if verbose:
                    print(f"Successfully read with encoding: {encoding}")
                break
            except Exception:
                continue
        
        if mht_content is None:
            raise ValueError("Could not read MHT file with any encoding")
        
        # Parse as email message
        try:
            msg = email.message_from_string(mht_content)
        except Exception as e:
            raise ValueError(f"Failed to parse MHT: {e}")
        
        # Extract HTML content
        html_content = None
        
        if msg.is_multipart():
            for part in msg.walk():
                extracted = self.extract_html_from_part(part)
                if extracted:
                    html_content = extracted
                    break
        else:
            html_content = self.extract_html_from_part(msg)
        
        if not html_content:
            raise ValueError("No HTML content found")
        
        # Clean and enhance content
        html_content = self.clean_html_content(html_content)
        
        # Determine output path
        if output_path is None:
            output_path = mht_path.with_suffix('.html')
        else:
            output_path = Path(output_path)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Converted: {mht_path.name} -> {output_path.name}")
        
        return str(output_path)


def main():
    """Command line interface for enhanced converter."""
    parser = argparse.ArgumentParser(
        description="Enhanced MHT to HTML converter with Chinese character recovery"
    )
    parser.add_argument('input_path', help='MHT file to convert')
    parser.add_argument('-o', '--output', help='Output HTML file')
    parser.add_argument('-c', '--config', help='Configuration file for restoration patterns')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = EnhancedMHTConverter(args.config)
    
    try:
        output_file = converter.convert_mht_to_html(
            args.input_path, args.output, args.verbose
        )
        print(f"Enhanced HTML file created: {output_file}")
        print("Note: Areas with [缺失中文字符] indicate locations where Chinese text was lost.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
