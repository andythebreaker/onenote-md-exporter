#!/usr/bin/env python3
"""
Binary MHT to HTML converter without restoration patterns.
Reads MHT as binary and handles specific encoding issues.
"""

import os
import sys
import email
from email.message import Message
import quopri
import base64
import re
from pathlib import Path
from typing import Optional
import argparse


class BinaryMHTConverter:
    """Binary MHT converter without restoration patterns."""
    
    def __init__(self):
        self.verbose = False
    
    def clean_binary_artifacts(self, content: str) -> str:
        """Clean specific binary artifacts from the content."""
        
        # Fix <= patterns (< followed by =)
        content = re.sub(r'<=', '<', content)
        
        # Remove E38081 sequences that appear after '>' (3E)
        # Pattern: '>' followed by E38081 encoding
        content = re.sub(r'>E38081', '>', content)
        content = re.sub(r'>=E3=80=81', '>', content)
        
        # Clean other common binary artifacts
        content = re.sub(r'=E3=80=81', '', content)  # Remove this specific sequence
        
        # Fix broken quoted-printable sequences
        content = re.sub(r'=([0-9A-F])(\r?\n)([0-9A-F])', r'=\1\3', content)
        
        if self.verbose:
            print("Cleaned binary artifacts")
        
        return content
    
    def decode_quoted_printable_binary(self, content: str) -> str:
        """Decode quoted-printable content from binary reading."""
        original_content = content
        
        try:
            # Clean binary artifacts first
            content = self.clean_binary_artifacts(content)
            
            # Handle soft line breaks more aggressively
            content = re.sub(r'=\r?\n\s*', '', content)
            content = re.sub(r'=\r?\n', '', content)
            
            # Fix broken hex sequences across lines
            content = re.sub(r'=([0-9A-F])\s*\r?\n\s*([0-9A-F])', r'=\1\2', content)
            
            # Basic quoted-printable fixes
            content = re.sub(r'=3D', '=', content)
            content = re.sub(r'=3E', '>', content)  # Fix > character
            content = re.sub(r'=3C', '<', content)  # Fix < character
            content = re.sub(r'=22', '"', content)
            content = re.sub(r'=20', ' ', content)
            
            if self.verbose:
                print("Applied basic QP fixes")
            
            # Standard quoted-printable decoding
            if '=' in content and re.search(r'=[0-9A-F]{2}', content):
                try:
                    # First pass: fix any remaining line break issues
                    lines = content.split('\n')
                    fixed_lines = []
                    for i, line in enumerate(lines):
                        line = line.rstrip('\r')
                        if line.endswith('=') and i + 1 < len(lines):
                            # Soft line break - join with next line
                            next_line = lines[i + 1].lstrip()
                            fixed_lines.append(line[:-1] + next_line)
                            lines[i + 1] = ''  # Mark as processed
                        elif line:  # Only add non-empty lines
                            fixed_lines.append(line)
                    
                    content = '\n'.join(fixed_lines)
                    
                    # Encode to latin-1 bytes first
                    encoded_bytes = content.encode('latin-1', errors='ignore')
                    # Decode quoted-printable
                    decoded_bytes = quopri.decodestring(encoded_bytes)
                    
                    # Try different encodings
                    for encoding in ['utf-8', 'big5', 'gb2312', 'shift_jis']:
                        try:
                            decoded_content = decoded_bytes.decode(encoding, errors='strict')
                            if self.verbose:
                                print(f"Successfully decoded with {encoding}")
                            return decoded_content
                        except UnicodeDecodeError:
                            continue
                    
                    # Fallback to UTF-8 with replacement
                    decoded_content = decoded_bytes.decode('utf-8', errors='replace')
                    if self.verbose:
                        print("Using UTF-8 with replacement characters")
                    return decoded_content
                    
                except Exception as e:
                    if self.verbose:
                        print(f"Standard QP decoding failed: {e}")
            
            return content
            
        except Exception as e:
            if self.verbose:
                print(f"Decoding failed: {e}")
            return original_content
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content from email part."""
        content_type = part.get_content_type()
        
        if content_type != 'text/html':
            return None
        
        if self.verbose:
            charset = part.get_content_charset() or 'unknown'
            print(f"Processing part: {content_type}, charset: {charset}")
        
        transfer_encoding = part.get('Content-Transfer-Encoding', '').lower()
        payload = part.get_payload()
        
        if transfer_encoding == 'quoted-printable':
            return self.decode_quoted_printable_binary(payload)
        elif transfer_encoding == 'base64':
            try:
                decoded_bytes = base64.b64decode(payload)
                # Try multiple encodings for base64 content
                for encoding in ['utf-8', 'big5', 'gb2312']:
                    try:
                        return decoded_bytes.decode(encoding, errors='strict')
                    except UnicodeDecodeError:
                        continue
                return decoded_bytes.decode('utf-8', errors='replace')
            except Exception:
                return payload
        else:
            if isinstance(payload, bytes):
                # Try multiple encodings for raw bytes
                for encoding in ['utf-8', 'big5', 'gb2312']:
                    try:
                        return payload.decode(encoding, errors='strict')
                    except UnicodeDecodeError:
                        continue
                return payload.decode('utf-8', errors='replace')
            return payload
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean HTML content without restoration patterns."""
        
        # Remove any remaining binary artifacts
        html_content = self.clean_binary_artifacts(html_content)
        
        # Clean up encoding artifacts
        html_content = re.sub(r'[��]+', '', html_content)
        
        # Standard HTML entity fixes only
        entity_fixes = {
            '&amp;': '&', 
            '&lt;': '<', 
            '&gt;': '>',
            '&quot;': '"', 
            '&apos;': "'", 
            '&nbsp;': ' '
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
        """Convert MHT to HTML using binary reading."""
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read MHT file as binary first, then decode
        try:
            with open(mht_path, 'rb') as f:
                mht_bytes = f.read()
            
            if verbose:
                print(f"Read {len(mht_bytes)} bytes from MHT file")
            
            # Try to decode as text with different encodings
            mht_content = None
            for encoding in ['utf-8', 'utf-8-sig', 'big5', 'gb2312', 'latin1', 'cp1252']:
                try:
                    mht_content = mht_bytes.decode(encoding, errors='replace')
                    if verbose:
                        print(f"Successfully decoded binary content with {encoding}")
                    break
                except Exception:
                    continue
            
            if mht_content is None:
                raise ValueError("Could not decode MHT binary content")
            
        except Exception as e:
            raise ValueError(f"Failed to read MHT file as binary: {e}")
        
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
        
        # Clean content without restoration patterns
        html_content = self.clean_html_content(html_content)
        
        # Determine output path
        if output_path is None:
            output_path = mht_path.with_suffix('.binary.html')
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
        description="Binary MHT to HTML converter without restoration patterns"
    )
    parser.add_argument('input_path', help='MHT file to convert')
    parser.add_argument('-o', '--output', help='Output HTML file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = BinaryMHTConverter()
    
    try:
        output_file = converter.convert_mht_to_html(
            args.input_path, args.output, args.verbose
        )
        print(f"Binary HTML file created: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
