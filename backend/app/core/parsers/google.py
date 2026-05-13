"""
Google Drive link parser implementation
"""
import re
from typing import List
from app.core.parsers.base import LinkParser, LinkInfo


class GoogleLinkParser(LinkParser):
    """Parser for Google Drive links (drive.google.com)"""
    
    def parse(self, text: str) -> List[LinkInfo]:
        """
        Extract Google Drive links from text
        
        Args:
            text: Input text containing potential Google Drive links
            
        Returns:
            List of LinkInfo objects for Google Drive links
        """
        links = []
        
        # Find all Google Drive file URLs
        file_pattern = re.compile(
            r'https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
            re.IGNORECASE
        )
        
        # Find all Google Drive folder URLs
        folder_pattern = re.compile(
            r'https?://drive\.google\.com/(?:folderview\?id=|drive/folders/)([a-zA-Z0-9_-]+)',
            re.IGNORECASE
        )
        
        # Find complete URLs for files
        file_matches = file_pattern.finditer(text)
        seen_urls = set()
        
        for match in file_matches:
            # Get the full URL by finding the start of the URL
            start = match.start()
            # Search backwards for http
            while start > 0 and text[start:start+4] not in ('http', 'HTTP'):
                start -= 1
            
            # Extract full URL
            end = match.end()
            url = text[start:end].rstrip('),.;')
            
            if url not in seen_urls:
                seen_urls.add(url)
                link_info = LinkInfo(
                    url=url,
                    provider='google',
                    type='file',
                    metadata={
                        'file_id': match.group(1),
                        'parsed_by': 'GoogleLinkParser'
                    }
                )
                links.append(link_info)
        
        # Find complete URLs for folders
        folder_matches = folder_pattern.finditer(text)
        
        for match in folder_matches:
            start = match.start()
            while start > 0 and text[start:start+4] not in ('http', 'HTTP'):
                start -= 1
            
            end = match.end()
            url = text[start:end].rstrip('),.;')
            
            if url not in seen_urls:
                seen_urls.add(url)
                link_info = LinkInfo(
                    url=url,
                    provider='google',
                    type='folder',
                    metadata={
                        'folder_id': match.group(1),
                        'parsed_by': 'GoogleLinkParser'
                    }
                )
                links.append(link_info)
        
        return links
