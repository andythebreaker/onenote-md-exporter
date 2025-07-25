#!/usr/bin/env python3
"""
Pure binary MHT converter - no restoration patterns, direct binary processing.
"""

import os
import sys
import email
import re
from pathlib import Path
from typing import Optional
import argparse


class PureBinaryMHTConverter:
    """Pure binary MHT converter without any restoration patterns."""
    
    def __init__(self):
        self.verbose = False
    
    def fix_broken_quoted_printable(self, content: str) -> str:
        """Fix broken quoted-printable sequences in binary content."""
        
        # Remove E38081 after > (as requested)
        content = re.sub(r'>E38081', '>', content)
        content = re.sub(r'>=E3=80=81', '>', content)
        
        # Fix <= back to <
        content = re.sub(r'<=', '<', content)
        
        # Handle soft line breaks more aggressively
        content = re.sub(r'=\r?\n\s*', '', content)
        content = re.sub(r'=\r?\n', '', content)
        
        # Fix broken hex sequences split across lines
        content = re.sub(r'=([0-9A-F])\s*\r?\n\s*([0-9A-F])', r'=\1\2', content)
        content = re.sub(r'=([0-9A-F])\s+([0-9A-F])', r'=\1\2', content)
        
        return content
    
    def extract_and_decode_html(self, mht_content: str) -> Optional[str]:
        """Extract HTML from MHT and decode properly."""
        
        try:
            # Parse as email
            msg = email.message_from_string(mht_content)
            
            # Find HTML part
            html_content = None
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/html':
                        payload = part.get_payload()
                        
                        # Process based on transfer encoding
                        encoding = part.get('Content-Transfer-Encoding', '').lower()
                        
                        if encoding == 'quoted-printable':
                            # Fix broken QP sequences first
                            payload = self.fix_broken_quoted_printable(payload)
                            
                            # Standard QP decode
                            import quopri
                            try:
                                encoded_bytes = payload.encode('latin-1', errors='ignore')
                                decoded_bytes = quopri.decodestring(encoded_bytes)
                                
                                # Try multiple encodings
                                for enc in ['utf-8', 'big5', 'gb2312']:
                                    try:
                                        html_content = decoded_bytes.decode(enc, errors='strict')
                                        if self.verbose:
                                            print(f"Decoded HTML with {enc}")
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                
                                if html_content is None:
                                    html_content = decoded_bytes.decode('utf-8', errors='replace')
                                    if self.verbose:
                                        print("Used UTF-8 with replacement")
                                        
                            except Exception as e:
                                if self.verbose:
                                    print(f"QP decode failed: {e}")
                                html_content = payload
                        
                        elif encoding == 'base64':
                            import base64
                            try:
                                decoded_bytes = base64.b64decode(payload)
                                for enc in ['utf-8', 'big5', 'gb2312']:
                                    try:
                                        html_content = decoded_bytes.decode(enc, errors='strict')
                                        break
                                    except UnicodeDecodeError:
                                        continue
                                if html_content is None:
                                    html_content = decoded_bytes.decode('utf-8', errors='replace')
                            except Exception:
                                html_content = payload
                        else:
                            html_content = payload
                        
                        if html_content:
                            break
            else:
                # Single part
                if msg.get_content_type() == 'text/html':
                    payload = msg.get_payload()
                    encoding = msg.get('Content-Transfer-Encoding', '').lower()
                    
                    if encoding == 'quoted-printable':
                        payload = self.fix_broken_quoted_printable(payload)
                        import quopri
                        try:
                            encoded_bytes = payload.encode('latin-1', errors='ignore')
                            decoded_bytes = quopri.decodestring(encoded_bytes)
                            html_content = decoded_bytes.decode('utf-8', errors='replace')
                        except Exception:
                            html_content = payload
                    else:
                        html_content = payload
            
            return html_content
            
        except Exception as e:
            if self.verbose:
                print(f"HTML extraction failed: {e}")
            return None
    
    def clean_html_only(self, html_content: str) -> str:
        """Clean HTML without any character restoration."""
        
        # Only basic HTML entity cleaning
        html_content = html_content.replace('&amp;', '&')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&quot;', '"')
        html_content = html_content.replace('&apos;', "'")
        html_content = html_content.replace('&nbsp;', ' ')
        
        # Add basic HTML structure if missing
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
        
        return html_content
    
    def convert_mht_to_html(self, mht_file_path: str, output_path: Optional[str] = None, 
                           verbose: bool = False) -> str:
        """Convert MHT to HTML using pure binary approach."""
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read as binary first
        try:
            with open(mht_path, 'rb') as f:
                mht_bytes = f.read()
            
            if verbose:
                print(f"Read {len(mht_bytes)} bytes")
            
            # Try different encodings to decode
            mht_content = None
            for encoding in ['utf-8', 'big5', 'gb2312', 'latin1', 'cp1252']:
                try:
                    mht_content = mht_bytes.decode(encoding, errors='replace')
                    if verbose:
                        print(f"Decoded with {encoding}")
                    break
                except Exception:
                    continue
            
            if mht_content is None:
                raise ValueError("Could not decode MHT file")
            
        except Exception as e:
            raise ValueError(f"Failed to read MHT: {e}")
        
        # Extract HTML
        html_content = self.extract_and_decode_html(mht_content)
        
        if not html_content:
            raise ValueError("No HTML content found")
        
        # Clean HTML (no restoration)
        html_content = self.clean_html_only(html_content)
        
        # Output
        if output_path is None:
            output_path = mht_path.with_suffix('.pure.html')
        else:
            output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Created: {output_path.name}")
        
        return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Pure binary MHT converter")
    parser.add_argument('input_path', help='MHT file to convert')
    parser.add_argument('-o', '--output', help='Output HTML file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = PureBinaryMHTConverter()
    
    try:
        output_file = converter.convert_mht_to_html(
            args.input_path, args.output, args.verbose
        )
        print(f"Pure binary HTML file: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
