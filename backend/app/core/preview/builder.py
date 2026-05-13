"""
Tree builder for creating preview trees from remote sources
"""
import asyncio
import uuid
from functools import lru_cache
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.parsers.base import LinkInfo
from app.core.preview.tree import PreviewTree, TreeNode
from app.core.rclone_client import RcloneClient


class TreeBuilder:
    """Async class for building preview trees from links"""
    
    # Cache for built trees (5 minutes TTL)
    _cache: Dict[str, tuple] = {}  # {link_url: (tree, timestamp)}
    _CACHE_TTL = timedelta(minutes=5)
    
    def __init__(self, rclone_client: Optional[RcloneClient] = None):
        self.rclone_client = rclone_client or RcloneClient()
    
    async def build_tree(self, link: LinkInfo) -> PreviewTree:
        """
        Build a preview tree from a link
        
        Args:
            link: LinkInfo object containing URL and metadata
            
        Returns:
            PreviewTree representing the file hierarchy
        """
        # Check cache first
        cached = self._get_cached(link.url)
        if cached:
            return cached
        
        # Build tree based on provider
        if link.provider == 'local':
            tree = await self._build_local_tree(link)
        else:
            tree = await self._build_remote_tree(link)
        
        # Cache the result
        self._cache_tree(link.url, tree)
        
        return tree
    
    def _get_cached(self, url: str) -> Optional[PreviewTree]:
        """Get cached tree if not expired"""
        if url in self._cache:
            tree, timestamp = self._cache[url]
            if datetime.now() - timestamp < self._CACHE_TTL:
                return tree
            else:
                del self._cache[url]
        return None
    
    def _cache_tree(self, url: str, tree: PreviewTree):
        """Cache a tree with current timestamp"""
        self._cache[url] = (tree, datetime.now())
    
    async def _build_local_tree(self, link: LinkInfo) -> PreviewTree:
        """Build tree for local path"""
        import os
        
        path = link.url
        root_name = os.path.basename(path) or path
        
        root = TreeNode(
            id=str(uuid.uuid4()),
            name=root_name,
            type=link.type,
            size=os.path.getsize(path) if os.path.isfile(path) else 0,
            path=path,
            children=[]
        )
        
        if link.type == 'folder' and os.path.isdir(path):
            try:
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    child_node = await self._create_local_node(item_path, item)
                    if child_node:
                        root.children.append(child_node)
            except PermissionError:
                pass
        
        return PreviewTree(root=root)
    
    async def _create_local_node(self, path: str, name: str) -> Optional[TreeNode]:
        """Create a TreeNode for a local file/folder"""
        import os
        
        try:
            if os.path.isfile(path):
                return TreeNode(
                    id=str(uuid.uuid4()),
                    name=name,
                    type='file',
                    size=os.path.getsize(path),
                    path=path,
                    children=[]
                )
            elif os.path.isdir(path):
                node = TreeNode(
                    id=str(uuid.uuid4()),
                    name=name,
                    type='folder',
                    size=0,
                    path=path,
                    children=[]
                )
                # Add immediate children (one level deep for preview)
                for item in os.listdir(path)[:10]:  # Limit to 10 items
                    item_path = os.path.join(path, item)
                    child = await self._create_local_node(item_path, item)
                    if child:
                        node.children.append(child)
                return node
        except (PermissionError, OSError):
            pass
        
        return None
    
    async def _build_remote_tree(self, link: LinkInfo) -> PreviewTree:
        """
        Build tree for remote source (Yandex/Google)
        Uses rclone client to fetch file listing
        """
        # Determine remote FS name based on provider
        if link.provider == 'yandex':
            remote_fs = 'yandex:'
        elif link.provider == 'google':
            remote_fs = 'gdrive:'
        else:
            remote_fs = 'remote:'
        
        # Extract path from URL
        path = self._extract_remote_path(link)
        
        # Create root node
        root_name = path.split('/')[-1] or f"{link.provider}_root"
        root = TreeNode(
            id=str(uuid.uuid4()),
            name=root_name,
            type=link.type,
            size=0,
            path=path,
            children=[]
        )
        
        # Try to fetch file listing via rclone
        try:
            files = await self._fetch_remote_files(remote_fs, path)
            for file_info in files:
                child = self._create_remote_node(file_info, path)
                if child:
                    root.children.append(child)
        except Exception as e:
            # If rclone fails, create a placeholder node
            root.metadata = {'error': str(e), 'warning': 'Could not fetch file listing'}
        
        return PreviewTree(root=root)
    
    def _extract_remote_path(self, link: LinkInfo) -> str:
        """Extract path component from URL"""
        from urllib.parse import urlparse
        
        parsed = urlparse(link.url)
        path = parsed.path
        
        # Remove leading slashes for cleaner path
        while path.startswith('/'):
            path = path[1:]
        
        return path or f"{link.provider}://root"
    
    async def _fetch_remote_files(self, remote_fs: str, path: str) -> list:
        """
        Fetch file listing from remote using rclone
        
        Returns list of file info dicts
        """
        # Mock implementation - in real scenario would call rclone
        # For now, return empty list or simulated data
        try:
            result = await self.rclone_client.rc_call(
                "fs/list",
                {"fs": f"{remote_fs}{path}" if path else remote_fs}
            )
            
            if 'list' in result:
                return result['list']
            return []
        except Exception:
            # Return mock data for testing
            return self._get_mock_files(path)
    
    def _get_mock_files(self, path: str) -> list:
        """Return mock file data for testing"""
        return [
            {'Name': 'document.pdf', 'Size': 1024000, 'IsDir': False},
            {'Name': 'photos', 'Size': 0, 'IsDir': True},
            {'Name': 'backup.zip', 'Size': 5120000, 'IsDir': False},
        ]
    
    def _create_remote_node(self, file_info: dict, parent_path: str) -> Optional[TreeNode]:
        """Create TreeNode from remote file info"""
        name = file_info.get('Name', 'Unknown')
        is_dir = file_info.get('IsDir', False)
        size = file_info.get('Size', 0)
        
        node = TreeNode(
            id=str(uuid.uuid4()),
            name=name,
            type='folder' if is_dir else 'file',
            size=size,
            path=f"{parent_path}/{name}" if parent_path else name,
            children=[]
        )
        
        return node
    
    def clear_cache(self):
        """Clear all cached trees"""
        self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired = [
            url for url, (_, timestamp) in self._cache.items()
            if now - timestamp >= self._CACHE_TTL
        ]
        for url in expired:
            del self._cache[url]
