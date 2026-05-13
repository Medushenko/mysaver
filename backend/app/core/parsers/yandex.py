"""
Yandex Disk link parser implementation
"""
import re
from typing import List
from app.core.parsers.base import LinkParser, LinkInfo


class YandexLinkParser(LinkParser):
    """Parser for Yandex Disk links (yadi.sk, disk.yandex.ru/com)"""
    
    def parse(self, text: str) -> List[LinkInfo]:
        """
        Extract Yandex Disk links from text
        
        Args:
            text: Input text containing potential Yandex links
            
        Returns:
            List of LinkInfo objects for Yandex links
        """
        links = []
        
        # Find all Yandex URLs directly
        yandex_url_pattern = re.compile(
            r'https?://(?:yadi\.sk|disk\.yandex\.(?:ru|com))(?:/[^\s]*)?',
            re.IGNORECASE
        )
        
        matches = yandex_url_pattern.findall(text)
        
        for url in matches:
            # Clean up URL
            url = url.rstrip('),.;')
            
            link_info = LinkInfo(
                url=url,
                provider='yandex',
                type=self._detect_yandex_type(url),
                metadata={
                    'parsed_by': 'YandexLinkParser'
                }
            )
            links.append(link_info)
        
        return links
