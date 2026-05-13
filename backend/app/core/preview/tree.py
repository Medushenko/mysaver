"""
Preview tree structures for file hierarchy representation
"""
import uuid
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TreeNode:
    """Node in the preview tree representing a file or folder"""
    id: str
    name: str
    type: str  # 'file' or 'folder'
    size: int = 0
    children: List['TreeNode'] = field(default_factory=list)
    checked: bool = True
    path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "children": [child.to_dict() for child in self.children],
            "checked": self.checked,
            "path": self.path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TreeNode':
        """Create TreeNode from dictionary"""
        children = [cls.from_dict(child) for child in data.get('children', [])]
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', 'Unknown'),
            type=data.get('type', 'file'),
            size=data.get('size', 0),
            children=children,
            checked=data.get('checked', True),
            path=data.get('path', '')
        )


@dataclass
class PreviewTree:
    """Tree structure representing file hierarchy for preview"""
    root: TreeNode
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire tree to dictionary for JSON serialization"""
        return self.root.to_dict()
    
    def filter_checked(self) -> 'PreviewTree':
        """
        Return a new tree with only checked nodes
        
        Returns:
            New PreviewTree containing only checked nodes
        """
        def filter_node(node: TreeNode) -> Optional[TreeNode]:
            if not node.checked:
                return None
            
            filtered_children = []
            for child in node.children:
                filtered_child = filter_node(child)
                if filtered_child:
                    filtered_children.append(filtered_child)
            
            # Create new node with filtered children
            return TreeNode(
                id=node.id,
                name=node.name,
                type=node.type,
                size=node.size,
                children=filtered_children,
                checked=node.checked,
                path=node.path
            )
        
        filtered_root = filter_node(self.root)
        if filtered_root is None:
            # Return empty tree if root is not checked
            filtered_root = TreeNode(
                id=str(uuid.uuid4()),
                name="root",
                type="folder",
                children=[]
            )
        
        return PreviewTree(root=filtered_root)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Calculate statistics for the tree
        
        Returns:
            Dictionary with total_files, total_size, total_folders
        """
        stats = {
            "total_files": 0,
            "total_folders": 0,
            "total_size": 0
        }
        
        def traverse(node: TreeNode):
            if node.type == 'folder':
                stats["total_folders"] += 1
            else:
                stats["total_files"] += 1
                stats["total_size"] += node.size
            
            for child in node.children:
                traverse(child)
        
        traverse(self.root)
        
        # Don't count root as a folder if it's just a container
        if self.root.type == 'folder' and not self.root.path:
            stats["total_folders"] -= 1
        
        return stats
    
    def find_node_by_id(self, node_id: str) -> Optional[TreeNode]:
        """Find a node by its ID"""
        def search(node: TreeNode) -> Optional[TreeNode]:
            if node.id == node_id:
                return node
            for child in node.children:
                result = search(child)
                if result:
                    return result
            return None
        
        return search(self.root)
    
    def toggle_node(self, node_id: str) -> bool:
        """Toggle the checked state of a node"""
        node = self.find_node_by_id(node_id)
        if node:
            node.checked = not node.checked
            return True
        return False
