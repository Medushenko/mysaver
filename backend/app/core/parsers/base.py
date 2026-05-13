"""
Base parser module for link extraction and validation
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import re
from urllib.parse import urlparse


@dataclass
class LinkInfo:
    """Information about extracted link"""
    url: str
    provider: str  # yandex|google|local
    type: str  # file|folder
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "url": self.url,
            "provider": self.provider,
            "type": self.type,
            "metadata": self.metadata
        }


class LinkParser(ABC):
    """Abstract base class for link parsers"""
    
    # Common regex patterns
    YANDEX_PATTERN = re.compile(
        r'https?://(?:yadi\.sk|disk\.yandex\.(?:ru|com))/(?:d/|i/)?([^\s]*)',
        re.IGNORECASE
    )
    GOOGLE_FILE_PATTERN = re.compile(
        r'https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        re.IGNORECASE
    )
    GOOGLE_FOLDER_PATTERN = re.compile(
        r'https?://drive\.google\.com/(?:folderview\?id=|drive/folders/)([a-zA-Z0-9_-]+)',
        re.IGNORECASE
    )
    LOCAL_UNIX_PATTERN = re.compile(
        r'^\/[\w\/\.\-]+$'
    )
    LOCAL_WINDOWS_PATTERN = re.compile(
        r'^[A-Za-z]:\\[\\w\.\-]+(?:\\[\\w\.\-]+)*$'
    )
    
    @abstractmethod
    def parse(self, text: str) -> List[LinkInfo]:
        """
        Parse text and extract links
        
        Args:
            text: Input text containing potential links
            
        Returns:
            List of LinkInfo objects
        """
        pass
    
    def _validate_url(self, url: str) -> bool:
        """Basic URL validation"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _is_local_path(self, path: str) -> bool:
        """Check if string is a valid local path"""
        return bool(
            self.LOCAL_UNIX_PATTERN.match(path) or 
            self.LOCAL_WINDOWS_PATTERN.match(path)
        )
    
    def _detect_yandex_type(self, url: str) -> str:
        """Detect if Yandex link is file or folder"""
        if '/d/' in url or 'yadi.sk/d/' in url:
            return 'file'
        elif '/i/' in url or 'yadi.sk/i/' in url:
            return 'folder'
        # Default to folder for root links
        return 'folder'
    
    def _detect_google_type(self, url: str) -> str:
        """Detect if Google Drive link is file or folder"""
        if '/file/d/' in url:
            return 'file'
        elif '/folderview' in url or '/drive/folders/' in url:
            return 'folder'
        return 'folder'
