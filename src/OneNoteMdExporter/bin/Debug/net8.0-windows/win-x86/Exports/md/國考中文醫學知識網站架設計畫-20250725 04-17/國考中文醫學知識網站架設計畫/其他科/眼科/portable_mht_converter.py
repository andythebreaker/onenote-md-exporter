#!/usr/bin/env python3
"""
Portable MHT to HTML converter with configurable character restoration.
This version uses external configuration for character mappings to maintain portability.
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


class ConfigurableMHTConverter:
    """MHT converter with configurable character restoration patterns."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.encoding = 'utf-8'
        self.default_charset = 'utf-8'
        self.verbose = False
        
        # Load configuration for character restoration
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
        
        # Return empty dict for no hardcoded patterns
        return {}
    
    def decode_quoted_printable(self, content: str) -> str:
        """Decode quoted-printable content with improved multi-byte handling."""
        try:
            # Remove soft line breaks first
            content = re.sub(r'=\r?\n', '', content)
            
            # Fix common HTML entities that appear in quoted-printable
            content = re.sub(r'=3D', '=', content)
            content = re.sub(r'=22', '"', content)
            content = re.sub(r'=20', ' ', content)
            
            # Enhanced multi-byte character handling
            # Look for sequences of =XX that represent UTF-8 encoded Chinese characters
            def decode_utf8_sequence(match):
                """Decode a sequence of =XX hex codes as UTF-8 bytes."""
                hex_sequence = match.group(0)
                # Extract all hex codes from the sequence
                hex_codes = re.findall(r'=([0-9A-F]{2})', hex_sequence)
                
                if not hex_codes:
                    return hex_sequence
                
                try:
                    # Convert hex codes to bytes
                    byte_data = bytes([int(code, 16) for code in hex_codes])
                    # Decode as UTF-8
                    decoded_text = byte_data.decode('utf-8', errors='strict')
                    return decoded_text
                except (ValueError, UnicodeDecodeError):
                    # If UTF-8 decoding fails, try other encodings
                    for encoding in ['big5', 'gb2312']:
                        try:
                            decoded_text = byte_data.decode(encoding, errors='strict')
                            return decoded_text
                        except UnicodeDecodeError:
                            continue
                    
                    # If all encodings fail, return the original sequence
                    return hex_sequence
            
            # Pattern to match sequences of =XX (especially those starting with high bytes)
            # This pattern looks for sequences of 1-4 hex codes that likely represent multi-byte chars
            multibyte_pattern = r'(?:=[8-9A-F][0-9A-F]){1,4}|(?:=[E][0-9A-F]=[0-9A-F][0-9A-F]=[0-9A-F][0-9A-F])'
            content = re.sub(multibyte_pattern, decode_utf8_sequence, content)
            
            # Standard quoted-printable decoding for remaining content
            try:
                # Only process content that looks like it needs quoted-printable decoding
                if '=' in content and re.search(r'=[0-9A-F]{2}', content):
                    # Encode as latin-1 for quopri processing
                    encoded_bytes = content.encode('latin-1', errors='ignore')
                    decoded_bytes = quopri.decodestring(encoded_bytes)
                    
                    # Try to decode with UTF-8 first
                    try:
                        result = decoded_bytes.decode('utf-8', errors='strict')
                        return result
                    except UnicodeDecodeError:
                        # Try other encodings
                        for encoding in ['big5', 'gb2312']:
                            try:
                                result = decoded_bytes.decode(encoding, errors='strict')
                                return result
                            except UnicodeDecodeError:
                                continue
                        
                        # Fallback with replacement characters
                        return decoded_bytes.decode('utf-8', errors='replace')
                else:
                    # Content doesn't need quoted-printable decoding
                    return content
                    
            except Exception as e:
                if self.verbose:
                    print(f"Standard quoted-printable decoding failed: {e}")
                # Manual hex replacement as fallback
                def replace_remaining_hex(match):
                    try:
                        hex_val = match.group(1)
                        byte_val = int(hex_val, 16)
                        if byte_val < 128:  # ASCII
                            return chr(byte_val)
                        else:
                            return match.group(0)  # Keep non-ASCII as-is
                    except:
                        return match.group(0)
                
                content = re.sub(r'=([0-9A-F]{2})', replace_remaining_hex, content)
                return content
                
        except Exception as e:
            if self.verbose:
                print(f"Warning: Quoted-printable decoding error: {e}")
            return content
    
    def apply_restoration_patterns(self, content: str) -> str:
        """Apply configurable character restoration patterns."""
        if not self.restoration_patterns:
            return content
        
        for pattern, replacement in self.restoration_patterns.items():
            try:
                content = re.sub(pattern, replacement, content)
            except Exception as e:
                if self.verbose:
                    print(f"Warning: Pattern '{pattern}' failed: {e}")
        
        return content
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML content with configurable restoration."""
        # Basic cleanup
        html_content = re.sub(r'=\r?\n', '', html_content)
        
        # Fix quoted-printable HTML artifacts
        html_content = re.sub(r'=3D', '=', html_content)
        html_content = re.sub(r'=22', '"', html_content)
        html_content = re.sub(r'=20', ' ', html_content)
        
        # Apply configurable restoration patterns
        html_content = self.apply_restoration_patterns(html_content)
        
        # Generic HTML entity fixes
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
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content from message part."""
        content_type = part.get_content_type()
        
        if content_type != 'text/html':
            return None
        
        # Get charset
        charset = part.get_content_charset() or self.default_charset
        self.encoding = charset
        
        if self.verbose:
            print(f"Processing part: {content_type}, charset: {charset}")
        
        # Get transfer encoding and payload
        transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
        payload = part.get_payload()
        
        if transfer_encoding == 'quoted-printable':
            return self.decode_quoted_printable(payload)
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
    
    def convert_mht_to_html(self, mht_file_path: str, output_path: Optional[str] = None, 
                           verbose: bool = False) -> str:
        """Convert MHT to HTML."""
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read MHT file
        try:
            with open(mht_path, 'r', encoding='utf-8', errors='replace') as f:
                mht_content = f.read()
        except Exception as e:
            # Fallback to other encodings
            for encoding in ['utf-8-sig', 'big5', 'gb2312', 'latin1']:
                try:
                    with open(mht_path, 'r', encoding=encoding, errors='replace') as f:
                        mht_content = f.read()
                    if verbose:
                        print(f"Used encoding: {encoding}")
                    break
                except:
                    continue
            else:
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
        
        # Clean content
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


def create_sample_config():
    """Create a sample configuration file for character restoration."""
    sample_config = {
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
    
    config_path = Path('mht_converter_config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    
    print(f"Sample configuration created: {config_path}")
    print("Edit this file to customize character restoration patterns.")


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Configurable MHT to HTML converter"
    )
    parser.add_argument('input_path', nargs='?', help='MHT file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-c', '--config', help='Configuration file for restoration patterns')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--create-config', action='store_true', 
                       help='Create sample configuration file')
    
    args = parser.parse_args()
    
    if args.create_config:
        create_sample_config()
        return
    
    if not args.input_path:
        parser.print_help()
        return
    
    converter = ConfigurableMHTConverter(args.config)
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
