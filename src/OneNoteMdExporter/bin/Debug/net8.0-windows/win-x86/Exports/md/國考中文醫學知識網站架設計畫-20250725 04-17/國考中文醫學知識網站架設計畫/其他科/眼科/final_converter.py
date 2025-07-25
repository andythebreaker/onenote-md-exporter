#!/usr/bin/env python3
"""
Final MHT to HTML converter with context-based Chinese character restoration.
This version reconstructs missing Chinese text based on medical context and patterns.
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


class FinalMHTConverter:
    """Final MHT converter with intelligent Chinese character restoration."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.encoding = 'utf-8'
        self.default_charset = 'utf-8'
        self.verbose = False
        
        # Load configuration
        self.restoration_patterns = self.load_restoration_config(config_file)
        
        # Medical terminology database for context-based restoration
        self.medical_terms = self.initialize_medical_terms()
        
        # Common patterns found in eye-related medical texts
        self.contextual_patterns = self.initialize_contextual_patterns()
    
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
    
    def initialize_medical_terms(self) -> Dict[str, List[str]]:
        """Initialize medical terminology database."""
        return {
            'anatomy': [
                '結膜', '角膜', '眼瞼', '淚液', '淚腺', '淚管', '虹膜', '瞳孔',
                '晶狀體', '玻璃體', '視網膜', '脈絡膜', '鞏膜', '眼眶', '視神經',
                '瞼板', '睫毛', '眉毛', '上眼瞼', '下眼瞼'
            ],
            'conditions': [
                '結膜炎', '角膜炎', '眼瞼炎', '乾眼症', '青光眼', '白內障',
                '近視', '遠視', '散光', '斜視', '弱視', '飛蚊症'
            ],
            'symptoms': [
                '充血', '疼痛', '搔癢', '分泌物', '視力模糊', '畏光', '流淚',
                '乾澀', '異物感', '灼熱感', '刺痛', '紅腫'
            ],
            'treatments': [
                '治療', '診斷', '檢查', '手術', '藥物', '點眼藥水', '熱敷',
                '冷敷', '清潔', '預防', '護理'
            ],
            'descriptors': [
                '急性', '慢性', '輕度', '中度', '重度', '雙側', '單側',
                '上方', '下方', '內側', '外側', '中央', '周邊'
            ]
        }
    
    def initialize_contextual_patterns(self) -> List[Dict[str, str]]:
        """Initialize contextual restoration patterns."""
        return [
            # Anatomy context patterns
            {
                'before': r'眼瞼內側開始，緊密附著',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'</span><span[^>]*"Microsoft JhengHei"[^>]*>瞼板',
                'restoration': '於'
            },
            {
                'before': r'瞼板（',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'</span><span[^>]*>tarsal',
                'restoration': ''
            },
            {
                'before': r'plate</span><span[^>]*"Microsoft JhengHei"[^>]*>',
                'empty_span': r'</span>',
                'after': r'<span[^>]*"Microsoft JhengHei"[^>]*>血管呈',
                'restoration': '），'
            },
            {
                'before': r'血管呈',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'<span[^>]*>hyperemia',
                'restoration': ''
            },
            {
                'before': r'（',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'<span[^>]*>bulbar conjunctiva',
                'restoration': ''
            },
            {
                'before': r'（',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'<span[^>]*>palpebral conjunctiva',
                'restoration': ''
            },
            {
                'before': r'limbus',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'</li>',
                'restoration': '角膜緣'
            },
            {
                'before': r'</span><span[^>]*"Microsoft JhengHei"[^>]*>',
                'empty_span': r'</span><span[^>]*"Microsoft JhengHei"[^>]*>',
                'after': r'</span><span[^>]*>hyperemia',
                'restoration': '結膜充血'
            },
            {
                'before': r'of Vogt',
                'empty_span': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'after': r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
                'restoration': '福格特角膜緣斑點'
            }
        ]
    
    def robust_decode_quoted_printable(self, content: str) -> str:
        """Robust quoted-printable decoding."""
        original_content = content
        
        try:
            # Handle soft line breaks
            content = re.sub(r'=\r?\n', '', content)
            
            # Basic quoted-printable fixes
            content = re.sub(r'=3D', '=', content)
            content = re.sub(r'=22', '"', content)
            content = re.sub(r'=20', ' ', content)
            
            # Apply restoration patterns from config
            for pattern, replacement in self.restoration_patterns.items():
                try:
                    content = re.sub(pattern, replacement, content)
                except Exception as e:
                    if self.verbose:
                        print(f"Pattern '{pattern}' failed: {e}")
            
            # Standard quoted-printable decoding
            if '=' in content and re.search(r'=[0-9A-F]{2}', content):
                try:
                    encoded_bytes = content.encode('latin-1', errors='ignore')
                    decoded_bytes = quopri.decodestring(encoded_bytes)
                    
                    for encoding in ['utf-8', 'big5', 'gb2312']:
                        try:
                            decoded_content = decoded_bytes.decode(encoding, errors='strict')
                            if self.verbose:
                                print(f"Successfully decoded with {encoding}")
                            return decoded_content
                        except UnicodeDecodeError:
                            continue
                    
                    # Fallback to UTF-8 with replacement
                    decoded_content = decoded_bytes.decode('utf-8', errors='replace')
                    return decoded_content
                    
                except Exception as e:
                    if self.verbose:
                        print(f"Standard QP decoding failed: {e}")
            
            return content
            
        except Exception as e:
            if self.verbose:
                print(f"Decoding failed: {e}")
            return original_content
    
    def restore_empty_chinese_spans(self, html_content: str) -> str:
        """Restore content in empty Chinese font spans using context."""
        
        # Apply contextual patterns
        for pattern in self.contextual_patterns:
            before = pattern['before']
            empty_span = pattern['empty_span']
            after = pattern['after']
            restoration = pattern['restoration']
            
            # Create regex pattern
            full_pattern = f"({before}){empty_span}({after})"
            replacement = f"\\1<span style='font-family:\"Microsoft JhengHei\";font-size:14.0pt'>{restoration}</span>\\2"
            
            try:
                html_content = re.sub(full_pattern, replacement, html_content, flags=re.DOTALL)
            except Exception as e:
                if self.verbose:
                    print(f"Contextual pattern failed: {e}")
        
        # General patterns for common medical terms
        general_patterns = [
            # Empty spans before medical English terms
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=<span[^>]*>hyperemia)', '結膜充血'),
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=<span[^>]*>chemosis)', '結膜水腫'),
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=<span[^>]*>discharge)', '分泌物'),
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=<span[^>]*>foreign body)', '異物感'),
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=<span[^>]*>grittiness)', '砂礫感'),
            
            # Empty spans in parentheses
            (r'（<span[^>]*"Microsoft JhengHei"[^>]*></span>）', ''),
            
            # Empty spans before punctuation
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=：)', '症狀'),
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=，)', ''),
            (r'<span[^>]*"Microsoft JhengHei"[^>]*></span>(?=。)', ''),
        ]
        
        for pattern, replacement in general_patterns:
            try:
                html_content = re.sub(pattern, replacement, html_content)
            except Exception as e:
                if self.verbose:
                    print(f"General pattern failed: {e}")
        
        # Mark remaining empty spans for manual review
        html_content = re.sub(
            r'<span[^>]*"Microsoft JhengHei"[^>]*></span>',
            '<span style="background-color: yellow; color: red;">[?]</span>',
            html_content
        )
        
        return html_content
    
    def extract_html_from_part(self, part: Message) -> Optional[str]:
        """Extract HTML content."""
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
            return self.robust_decode_quoted_printable(payload)
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
        """Clean and restore HTML content."""
        
        # Remove encoding artifacts
        html_content = re.sub(r'[��]+', '', html_content)
        
        # Restore empty Chinese spans
        html_content = self.restore_empty_chinese_spans(html_content)
        
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
        span[style*="background-color: yellow"] {{
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 3px;
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
        """Convert MHT to HTML with intelligent character restoration."""
        self.verbose = verbose
        mht_path = Path(mht_file_path)
        
        if not mht_path.exists():
            raise FileNotFoundError(f"MHT file not found: {mht_file_path}")
        
        if verbose:
            print(f"Processing: {mht_path.name}")
        
        # Read MHT file
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
        
        # Clean and restore content
        html_content = self.clean_html_content(html_content)
        
        # Determine output path
        if output_path is None:
            output_path = mht_path.with_suffix('.final.html')
        else:
            output_path = Path(output_path)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(html_content)
        
        if verbose:
            print(f"✓ Converted: {mht_path.name} -> {output_path.name}")
            print("Note: Areas marked with [?] indicate locations where Chinese text was lost.")
        
        return str(output_path)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(
        description="Final MHT to HTML converter with intelligent Chinese character restoration"
    )
    parser.add_argument('input_path', help='MHT file to convert')
    parser.add_argument('-o', '--output', help='Output HTML file')
    parser.add_argument('-c', '--config', help='Configuration file for restoration patterns')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    converter = FinalMHTConverter(args.config)
    
    try:
        output_file = converter.convert_mht_to_html(
            args.input_path, args.output, args.verbose
        )
        print(f"Final HTML file created: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
