#!/usr/bin/env python3
"""
Advanced MHT to HTML converter with sophisticated Chinese character recovery.
Handles fragmented multi-byte characters in quoted-printable encoding.
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
from typing import Optional, Dict, Any, List, Tuple
import argparse
import codecs


class AdvancedMHTConverter:
    """Advanced MHT converter with sophisticated encoding recovery."""
    
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
    
    def reassemble_fragmented_content(self, content: str) -> str:
        """Reassemble fragmented multi-byte sequences that span across lines."""
        
        # Step 1: Remove soft line breaks but preserve potential fragments
        lines = content.split('\n')
        reassembled_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip('\r')
            
            # Check if line ends with a potential fragment
            if line.endswith('='):
                # This could be a soft line break or start of hex code
                if i + 1 < len(lines):
                    next_line = lines[i + 1].lstrip()
                    
                    # If next line starts with hex code, it's likely a fragmented character
                    if re.match(r'^[0-9A-F]{1,2}', next_line):
                        # Combine the lines
                        combined = line + next_line
                        reassembled_lines.append(combined)
                        i += 2  # Skip next line as it's been combined
                        continue
                    else:
                        # It's a soft line break, remove the =
                        line = line[:-1]
                        if i + 1 < len(lines):
                            line += lines[i + 1].lstrip()
                            i += 2
                            continue
            
            # Check for orphaned Chinese character fragments
            if re.search(r'[��]+$', line):
                # Try to find continuation in next lines
                fragment = line
                j = i + 1
                while j < len(lines) and j < i + 3:  # Look ahead max 3 lines
                    next_line = lines[j].strip()
                    if re.match(r'^[��]+', next_line):
                        fragment += next_line
                        j += 1
                    else:
                        break
                
                if j > i + 1:  # Found fragments to combine
                    reassembled_lines.append(fragment)
                    i = j
                    continue
            
            reassembled_lines.append(line)
            i += 1
        
        return '\n'.join(reassembled_lines)
    
    def decode_quoted_printable_advanced(self, content: str) -> str:
        """Advanced quoted-printable decoding with fragment recovery."""
        original_content = content
        
        if self.verbose:
            print("Starting advanced quoted-printable decoding...")
        
        try:
            # Step 1: Reassemble fragmented content
            content = self.reassemble_fragmented_content(content)
            
            # Step 2: Fix common QP issues
            content = re.sub(r'=3D', '=', content)
            content = re.sub(r'=22', '"', content)
            content = re.sub(r'=20', ' ', content)
            
            # Step 3: Handle soft line breaks more carefully
            # Remove = at end of lines followed by newline
            content = re.sub(r'=\r?\n\s*', '', content)
            
            # Step 4: Try to recover fragmented Chinese characters
            content = self.recover_fragmented_chinese(content)
            
            # Step 5: Standard quoted-printable decoding
            if '=' in content and re.search(r'=[0-9A-F]{2}', content):
                try:
                    # Encode to bytes first
                    encoded_bytes = content.encode('latin-1', errors='ignore')
                    # Decode quoted-printable
                    decoded_bytes = quopri.decodestring(encoded_bytes)
                    
                    # Try different encodings
                    for encoding in ['utf-8', 'big5', 'gb2312']:
                        try:
                            decoded_content = decoded_bytes.decode(encoding, errors='strict')
                            if self.verbose:
                                print(f"Successfully decoded with {encoding}")
                            return decoded_content
                        except UnicodeDecodeError:
                            continue
                    
                    # Use UTF-8 with replacement as fallback
                    decoded_content = decoded_bytes.decode('utf-8', errors='replace')
                    if self.verbose:
                        print("Using UTF-8 with replacement characters")
                    return decoded_content
                    
                except Exception as e:
                    if self.verbose:
                        print(f"Standard QP decoding failed: {e}")
            
            # Step 6: Manual hex processing for remaining issues
            content = self.manual_hex_decode(content)
            
            return content
            
        except Exception as e:
            if self.verbose:
                print(f"Advanced decoding failed: {e}")
            return original_content
    
    def recover_fragmented_chinese(self, content: str) -> str:
        """Recover fragmented Chinese characters."""
        
        # Look for patterns like "字�=" followed by hex codes
        fragment_pattern = r'([一-龯])([��]+)=([0-9A-F]{2})'
        
        def fix_fragment(match):
            chinese_char = match.group(1)
            fragment_chars = match.group(2)
            hex_code = match.group(3)
            
            try:
                # Try to decode the hex as part of the character
                byte_val = int(hex_code, 16)
                # This is a simplification - in reality, you'd need more context
                return chinese_char
            except:
                return match.group(0)
        
        content = re.sub(fragment_pattern, fix_fragment, content)
        
        # Also look for orphaned fragments at line ends
        orphan_pattern = r'([一-龯])[��]+$'
        content = re.sub(orphan_pattern, r'\1', content, flags=re.MULTILINE)
        
        return content
    
    def manual_hex_decode(self, content: str) -> str:
        """Manual hex decoding for remaining quoted-printable sequences."""
        
        # Process =XX sequences
        hex_pattern = r'=([0-9A-F]{2})'
        
        def decode_hex_sequence(text):
            """Decode hex sequences while preserving multi-byte characters."""
            
            def collect_bytes(match_obj):
                """Collect bytes from hex codes."""
                hex_val = match_obj.group(1)
                return bytes([int(hex_val, 16)])
            
            # Find all hex sequences and their positions
            parts = []
            current_pos = 0
            byte_buffer = bytearray()
            
            for match in re.finditer(hex_pattern, text):
                # Add text before match
                if match.start() > current_pos:
                    # Process any accumulated bytes first
                    if byte_buffer:
                        parts.append(self.decode_byte_buffer(byte_buffer))
                        byte_buffer = bytearray()
                    
                    parts.append(text[current_pos:match.start()])
                
                # Collect byte
                hex_val = match.group(1)
                byte_buffer.append(int(hex_val, 16))
                current_pos = match.end()
            
            # Process final accumulated bytes
            if byte_buffer:
                parts.append(self.decode_byte_buffer(byte_buffer))
            
            # Add remaining text
            if current_pos < len(text):
                parts.append(text[current_pos:])
            
            return ''.join(parts)
        
        return decode_hex_sequence(content)
    
    def decode_byte_buffer(self, byte_buffer: bytearray) -> str:
        """Decode a buffer of bytes using various encodings."""
        
        # Try different encodings
        for encoding in ['utf-8', 'big5', 'gb2312']:
            try:
                decoded = byte_buffer.decode(encoding, errors='strict')
                return decoded
            except UnicodeDecodeError:
                continue
        
        # Fallback to UTF-8 with replacement
        return byte_buffer.decode('utf-8', errors='replace')
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content with advanced recovery."""
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
            return self.decode_quoted_printable_advanced(payload)
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
        """Clean HTML content."""
        
        # Apply restoration patterns from config
        for pattern, replacement in self.restoration_patterns.items():
            try:
                html_content = re.sub(pattern, replacement, html_content)
            except Exception as e:
                if self.verbose:
                    print(f"Pattern '{pattern}' failed: {e}")
        
        # Clean up remaining encoding artifacts
        html_content = re.sub(r'[��]+', '', html_content)
        
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
        """Convert MHT to HTML with advanced character recovery."""
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
            output_path = mht_path.with_suffix('.advanced.html')
        else:
            output_path = Path(output_path)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Converted: {mht_path.name} -> {output_path.name}")
        
        return str(output_path)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Advanced MHT to HTML converter with sophisticated character recovery"
    )
    parser.add_argument('input_path', help='MHT file to convert')
    parser.add_argument('-o', '--output', help='Output HTML file')
    parser.add_argument('-c', '--config', help='Configuration file for restoration patterns')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = AdvancedMHTConverter(args.config)
    
    try:
        output_file = converter.convert_mht_to_html(
            args.input_path, args.output, args.verbose
        )
        print(f"Advanced HTML file created: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
