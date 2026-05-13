"""
Local path parser implementation
"""
import re
import os
from typing import List
from app.core.parsers.base import LinkParser, LinkInfo


class LocalPathParser(LinkParser):
    """Parser for local file system paths (Unix and Windows)"""
    
    def parse(self, text: str) -> List[LinkInfo]:
        """
        Extract local paths from text
        
        Args:
            text: Input text containing potential local paths
            
        Returns:
            List of LinkInfo objects for local paths
        """
        links = []
        
        # Split text by whitespace to find potential paths
        tokens = text.split()
        
        for token in tokens:
            # Clean up trailing punctuation
            clean_token = token.rstrip('),.;')
            
            if self._is_local_path(clean_token):
                # Determine if it's a file or folder
                path_type = self._detect_path_type(clean_token)
                
                link_info = LinkInfo(
                    url=clean_token,
                    provider='local',
                    type=path_type,
                    metadata={
                        'absolute': os.path.isabs(clean_token),
                        'exists': os.path.exists(clean_token),
                        'parsed_by': 'LocalPathParser'
                    }
                )
                links.append(link_info)
        
        return links
    
    def _detect_path_type(self, path: str) -> str:
        """Detect if path is a file or folder"""
        if os.path.isfile(path):
            return 'file'
        elif os.path.isdir(path):
            return 'folder'
        else:
            # If doesn't exist, guess by extension
            if '.' in os.path.basename(path):
                return 'file'
            return 'folder'
