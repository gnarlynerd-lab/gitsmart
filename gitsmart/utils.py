"""
Utilities - Helper functions for GitSmart
"""

import re
from typing import List, Dict, Any
from pathlib import Path


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text using simple heuristics"""
    # Remove common words and extract meaningful terms
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Extract words (alphanumeric sequences)
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter out stop words and short words
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords[:20]  # Limit to top 20


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity based on common keywords"""
    keywords1 = set(extract_keywords(text1))
    keywords2 = set(extract_keywords(text2))
    
    if not keywords1 and not keywords2:
        return 0.0
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    return len(intersection) / len(union) if union else 0.0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem usage"""
    # Replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:197] + "..."
    
    return sanitized


def is_binary_file(filepath: Path) -> bool:
    """Check if a file is likely binary (not text)"""
    binary_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico',
        '.mp3', '.wav', '.mp4', '.avi', '.mov', '.wmv',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.exe', '.dll', '.so', '.dylib',
        '.class', '.jar', '.war',
        '.pyc', '.pyo'
    }
    
    if filepath.suffix.lower() in binary_extensions:
        return True
    
    # Check first few bytes for binary content
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            # If there are null bytes, it's likely binary
            if b'\x00' in chunk:
                return True
            # If more than 30% non-printable characters, consider binary
            non_printable = sum(1 for byte in chunk if byte < 32 and byte not in (9, 10, 13))
            if len(chunk) > 0 and non_printable / len(chunk) > 0.3:
                return True
    except (OSError, IOError):
        return True  # If we can't read it, assume binary
    
    return False


def extract_commit_urls(text: str, repo_url: str = None) -> List[str]:
    """Extract commit hashes and convert to URLs if repo URL provided"""
    # Find commit hashes (7-40 character hex strings)
    commit_pattern = r'\b[0-9a-f]{7,40}\b'
    commits = re.findall(commit_pattern, text)
    
    if not repo_url or not commits:
        return commits
    
    # Convert to GitHub/GitLab URLs
    urls = []
    for commit in commits:
        if 'github.com' in repo_url:
            url = f"{repo_url}/commit/{commit}"
        elif 'gitlab.com' in repo_url:
            url = f"{repo_url}/-/commit/{commit}"
        else:
            url = commit  # Just return the hash if unknown hosting
        urls.append(url)
    
    return urls


def parse_git_date(date_string: str) -> str:
    """Parse git date string into human readable format"""
    try:
        from datetime import datetime
        
        # Git uses various date formats, try to parse common ones
        formats = [
            '%Y-%m-%d %H:%M:%S %z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d',
            '%a %b %d %H:%M:%S %Y %z'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                return dt.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                continue
        
        # If parsing fails, return original string
        return date_string
        
    except ImportError:
        return date_string


def highlight_keywords(text: str, keywords: List[str]) -> str:
    """Highlight keywords in text (for terminal output)"""
    if not keywords:
        return text
    
    highlighted = text
    for keyword in keywords:
        # Use simple bold formatting
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        highlighted = pattern.sub(f"**{keyword}**", highlighted)
    
    return highlighted


def estimate_reading_time(text: str) -> str:
    """Estimate reading time for text"""
    words = len(text.split())
    minutes = max(1, words // 200)  # Average reading speed ~200 wpm
    
    if minutes == 1:
        return "1 minute read"
    else:
        return f"{minutes} minute read"