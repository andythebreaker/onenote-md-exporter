#!/usr/bin/env python3
"""
Generic MHT to HTML converter with improved encoding handling.
This version focuses on better encoding detection and processing
without hardcoded character mappings for better portability.
"""

import os
import sys
import email
from email.message import Message
import quopri
import base64
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import argparse


class EncodingDetector:
    """Generic encoding detection and fixing utilities."""
    
    @staticmethod
    def detect_encoding(content: bytes) -> str:
        """Detect encoding using heuristics and common patterns."""
        # Common encodings to try in order of preference
        encodings = ['utf-8', 'utf-8-sig', 'big5', 'gb2312', 'shift_jis', 'latin1']
        
        for encoding in encodings:
            try:
                decoded = content.decode(encoding)
                # Score the encoding based on presence of valid characters
                score = EncodingDetector._score_encoding(decoded, encoding)
                if score > 0.8:  # High confidence threshold
                    return encoding
            except UnicodeDecodeError:
                continue
        
        return 'utf-8'  # Default fallback
    
    @staticmethod
    def _score_encoding(decoded_text: str, encoding: str) -> float:
        """Score an encoding based on text characteristics."""
        score = 0.0
        total_chars = len(decoded_text)
        
        if total_chars == 0:
            return 0.0
        
        # Count valid characters vs replacement characters
        replacement_chars = decoded_text.count('�')
        valid_char_ratio = (total_chars - replacement_chars) / total_chars
        score += valid_char_ratio * 0.5
        
        # Bonus for CJK characters in CJK encodings
        if encoding in ['utf-8', 'big5', 'gb2312', 'shift_jis']:
            cjk_chars = sum(1 for char in decoded_text if '\u4e00' <= char <= '\u9fff')
            if cjk_chars > 0:
                score += min(cjk_chars / total_chars, 0.3)
        
        # Penalty for too many control characters
        control_chars = sum(1 for char in decoded_text if ord(char) < 32 and char not in '\n\r\t')
        if control_chars > total_chars * 0.1:
            score -= 0.2
        
        return min(score, 1.0)


class GenericMHTConverter:
    """Generic MHT to HTML converter with improved encoding handling."""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self.default_charset = 'utf-8'
        self.verbose = False
    
    def decode_quoted_printable_advanced(self, content: str) -> str:
        """Advanced quoted-printable decoding with multi-byte character support."""
        try:
            # Remove soft line breaks
            content = re.sub(r'=\r?\n', '', content)
            
            # Fix common quoted-printable HTML artifacts first
            content = re.sub(r'=3D', '=', content)
            content = re.sub(r'=22', '"', content)
            content = re.sub(r'=20', ' ', content)
            
            # Standard quoted-printable decoding
            try:
                # Use quopri module for standard decoding
                encoded_bytes = content.encode('latin-1', errors='ignore')
                decoded_bytes = quopri.decodestring(encoded_bytes)
                
                # Try different encodings to decode the result
                for encoding in ['utf-8', 'big5', 'gb2312']:
                    try:
                        result = decoded_bytes.decode(encoding, errors='strict')
                        return result
                    except UnicodeDecodeError:
                        continue
                
                # Fallback with error replacement
                return decoded_bytes.decode('utf-8', errors='replace')
                
            except Exception as e:
                if self.verbose:
                    print(f"Standard QP decoding failed: {e}")
                
                # Fallback: manual processing
                # Handle remaining =XX patterns
                def replace_hex(match):
                    try:
                        hex_val = match.group(1)
                        return chr(int(hex_val, 16))
                    except:
                        return match.group(0)
                
                content = re.sub(r'=([0-9A-F]{2})', replace_hex, content)
                return content
                
        except Exception as e:
            if self.verbose:
                print(f"Warning: Quoted-printable decoding error: {e}")
            return content
    
    def fix_encoding_artifacts(self, content: str) -> str:
        """Fix common encoding artifacts using generic approaches."""
        
        # Fix HTML entities
        entity_map = {
            '&amp;': '&', '&lt;': '<', '&gt;': '>', 
            '&quot;': '"', '&apos;': "'", '&nbsp;': ' '
        }
        
        for entity, char in entity_map.items():
            content = content.replace(entity, char)
        
        # Attempt to fix double-encoding issues
        try:
            # Check if content might be double-encoded
            if content.count('�') > len(content) * 0.05:  # High corruption ratio
                # Try re-encoding/decoding cycle
                test_bytes = content.encode('latin-1', errors='ignore')
                try:
                    fixed_content = test_bytes.decode('utf-8', errors='strict')
                    if fixed_content.count('�') < content.count('�'):
                        content = fixed_content
                except UnicodeDecodeError:
                    pass
        except Exception:
            pass
        
        return content
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content with improved encoding handling."""
        content_type = part.get_content_type()
        
        if content_type != 'text/html':
            return None
        
        # Get charset
        charset = part.get_content_charset() or self.default_charset
        self.encoding = charset
        
        if self.verbose:
            print(f"Processing part: {content_type}, charset: {charset}")
        
        # Get transfer encoding
        transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
        payload = part.get_payload()
        
        if transfer_encoding == 'quoted-printable':
            return self.decode_quoted_printable_advanced(payload)
        elif transfer_encoding == 'base64':
            try:
                decoded_bytes = base64.b64decode(payload)
                detected_encoding = EncodingDetector.detect_encoding(decoded_bytes)
                return decoded_bytes.decode(detected_encoding, errors='replace')
            except Exception:
                return payload
        else:
            # Handle plain content
            if isinstance(payload, bytes):
                detected_encoding = EncodingDetector.detect_encoding(payload)
                return payload.decode(detected_encoding, errors='replace')
            return payload
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML content with generic fixes."""
        # Basic cleanup
        html_content = re.sub(r'=\r?\n', '', html_content)
        
        # Fix quoted-printable artifacts
        html_content = re.sub(r'=([0-9A-F]{2})', 
                             lambda m: chr(int(m.group(1), 16)), html_content)
        
        # Apply generic encoding fixes
        html_content = self.fix_encoding_artifacts(html_content)
        
        # Ensure proper HTML structure
        if not re.search(r'<!DOCTYPE|<html', html_content, re.IGNORECASE):
            html_content = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        """Convert MHT to HTML with improved encoding handling."""
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read with encoding detection
        try:
            with open(mht_path, 'rb') as f:
                raw_content = f.read()
            
            detected_encoding = EncodingDetector.detect_encoding(raw_content)
            if verbose:
                print(f"Detected encoding: {detected_encoding}")
            
            mht_content = raw_content.decode(detected_encoding, errors='replace')
            
        except Exception as e:
            if verbose:
                print(f"Encoding detection failed: {e}")
            with open(mht_path, 'r', encoding='utf-8', errors='replace') as f:
                mht_content = f.read()
        
        # Parse email message
        try:
            msg = email.message_from_string(mht_content)
        except Exception as e:
            raise ValueError(f"Failed to parse MHT: {e}")
        
        # Extract HTML
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
        
        # Clean content
        html_content = self.clean_html_content(html_content)
        
        # Output
        if output_path is None:
            output_path = mht_path.with_suffix('.html')
        else:
            output_path = Path(output_path)
        
        # Write with UTF-8 BOM for maximum compatibility
        with open(output_path, 'w', encoding='utf-8-sig', newline='\n') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Converted: {mht_path.name} -> {output_path.name}")
        
        return str(output_path)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Generic MHT to HTML converter with improved encoding support"
    )
    parser.add_argument('input_path', help='MHT file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = GenericMHTConverter()
    input_path = Path(args.input_path)
    
    try:
        if input_path.is_file() and input_path.suffix.lower() == '.mht':
            # Single file
            output_file = converter.convert_mht_to_html(
                str(input_path), args.output, args.verbose
            )
            print(f"HTML file created: {output_file}")
            
        elif input_path.is_dir():
            # Directory
            mht_files = list(input_path.glob('*.mht'))
            
            if not mht_files:
                print("No MHT files found")
                return
            
            print(f"Converting {len(mht_files)} files...")
            
            success_count = 0
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
                    print(f"Failed: {mht_file.name} - {e}")
            
            print(f"Successfully converted: {success_count}/{len(mht_files)}")
            
        else:
            print("Input must be MHT file or directory")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
