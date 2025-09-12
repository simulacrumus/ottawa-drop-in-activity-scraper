# =============================================================================
#  Project:   City of Ottawa Drop-in Activity Scraper
#  File:      utility.py
#  Author:    Emrah Kinay
#  Created:   2025-09-12
#  License:   MIT
#
#  Description:
#      Utility functions
# =============================================================================

import re
import json
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'[\u00a0\n\t\r]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def clean_html_for_llm(html: str, max_length: int = 10000) -> str:
        # Remove unnecessary attributes and whitespace
        cleaned = re.sub(r'\s+', ' ', html)
        cleaned = re.sub(r'(class|id|style)="[^"]*"', '', cleaned)
        cleaned = re.sub(r'>\s+<', '><', cleaned)
        # Truncate if too long
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "..."
        return cleaned

def robust_json_extract(text: str, return_type: str = 'list') -> any:
    if not text:
        return [] if return_type == 'list' else {}
        
    # Clean markdown and extra text
    cleaned = re.sub(r'```(?:json)?\s*(.*?)```', r'\1', text, flags=re.DOTALL)
    cleaned = re.sub(r'^[^{\[]*([{\[].*[}\]])[^}\]]*$', r'\1', cleaned, flags=re.DOTALL)
    cleaned = cleaned.strip()
    
    # Try direct parsing first
    try:
        data = json.loads(cleaned)
        if return_type == 'list' and isinstance(data, list):
            return data
        elif return_type == 'dict' and isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    
    # Try regex extraction for arrays
    if return_type == 'list':
        # Look for array patterns
        array_patterns = [
            r'\[\s*\{.*?\}\s*\]',  # Complete array
            r'\{.*?\}(?:\s*,\s*\{.*?\})*'  # Multiple objects
        ]
        
        for pattern in array_patterns:
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                try:
                    # If it's not wrapped in [], wrap it
                    matched_text = match.group()
                    if not matched_text.strip().startswith('['):
                        matched_text = f"[{matched_text}]"
                    return json.loads(matched_text)
                except json.JSONDecodeError:
                    continue
    
    logger.debug(f"Failed to extract JSON: {text[:200]}...")
    return [] if return_type == 'list' else {}

def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes, secs = divmod(seconds, 60)
        return f"{int(minutes)}m {secs:.1f}s"
    else:
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {secs:.0f}s"