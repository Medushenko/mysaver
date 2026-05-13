"""
Conflict resolution logic for file operations
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class ConflictPolicy(str, Enum):
    """Policy for handling file conflicts"""
    SKIP = "skip"  # Skip the file, don't copy
    OVERWRITE = "overwrite"  # Overwrite destination file
    KEEP_BOTH = "keep_both"  # Keep both files (rename source)
    RENAME = "rename"  # Rename the new file with suffix


@dataclass
class FileInfo:
    """Information about a file involved in conflict"""
    path: str
    name: str
    size: int
    checksum: Optional[str] = None
    modified_time: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "checksum": self.checksum,
            "modified_time": self.modified_time
        }


@dataclass
class ResolutionResult:
    """Result of conflict resolution"""
    action_taken: str  # 'skipped', 'overwritten', 'renamed', 'copied'
    new_path: Optional[str] = None
    checksum_match: bool = False
    warning: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "action_taken": self.action_taken,
            "new_path": self.new_path,
            "checksum_match": self.checksum_match,
            "warning": self.warning
        }


class ConflictResolver:
    """Resolves file conflicts based on policy"""
    
    @staticmethod
    def resolve(
        src: FileInfo,
        dst: FileInfo,
        policy: ConflictPolicy
    ) -> ResolutionResult:
        """
        Resolve a conflict between source and destination files
        
        Args:
            src: Source file information
            dst: Destination file information
            policy: Conflict resolution policy
            
        Returns:
            ResolutionResult describing the action taken
        """
        # Check if files are identical
        checksum_match = (
            src.checksum is not None and 
            dst.checksum is not None and 
            src.checksum == dst.checksum
        )
        
        if checksum_match:
            # Files are identical, no need to copy
            return ResolutionResult(
                action_taken='skipped',
                new_path=dst.path,
                checksum_match=True,
                warning=None
            )
        
        if policy == ConflictPolicy.SKIP:
            return ResolutionResult(
                action_taken='skipped',
                new_path=dst.path,
                checksum_match=False,
                warning=f"Skipped '{src.name}' - destination exists"
            )
        
        elif policy == ConflictPolicy.OVERWRITE:
            return ResolutionResult(
                action_taken='overwritten',
                new_path=dst.path,
                checksum_match=False,
                warning=None
            )
        
        elif policy == ConflictPolicy.KEEP_BOTH:
            # Generate new name for source file
            new_name = ConflictResolver._generate_keep_both_name(src.name)
            new_path = f"{dst.path.rsplit('/', 1)[0]}/{new_name}" if '/' in dst.path else new_path
            
            return ResolutionResult(
                action_taken='renamed',
                new_path=new_path,
                checksum_match=False,
                warning=f"Kept both files, renamed to '{new_name}'"
            )
        
        elif policy == ConflictPolicy.RENAME:
            # Generate renamed file with suffix
            new_name = ConflictResolver._generate_rename(src.name)
            new_path = f"{dst.path.rsplit('/', 1)[0]}/{new_name}" if '/' in dst.path else new_path
            
            return ResolutionResult(
                action_taken='renamed',
                new_path=new_path,
                checksum_match=False,
                warning=f"Renamed to '{new_name}' to avoid conflict"
            )
        
        # Default: skip
        return ResolutionResult(
            action_taken='skipped',
            new_path=dst.path,
            checksum_match=False,
            warning="Unknown policy, defaulting to skip"
        )
    
    @staticmethod
    def _generate_keep_both_name(original_name: str) -> str:
        """Generate a name for keep_both policy"""
        import time
        timestamp = int(time.time())
        
        if '.' in original_name:
            name_parts = original_name.rsplit('.', 1)
            return f"{name_parts[0]}_copy_{timestamp}.{name_parts[1]}"
        else:
            return f"{original_name}_copy_{timestamp}"
    
    @staticmethod
    def _generate_rename(original_name: str, counter: int = 1) -> str:
        """Generate a renamed file with counter suffix"""
        if '.' in original_name:
            name_parts = original_name.rsplit('.', 1)
            return f"{name_parts[0]}_{counter}.{name_parts[1]}"
        else:
            return f"{original_name}_{counter}"
    
    @staticmethod
    def find_available_name(
        original_name: str,
        existing_names: set,
        policy: ConflictPolicy = ConflictPolicy.RENAME
    ) -> str:
        """
        Find an available name that doesn't conflict with existing names
        
        Args:
            original_name: Original file name
            existing_names: Set of existing file names in destination
            policy: Naming policy to use
            
        Returns:
            Available file name
        """
        if original_name not in existing_names:
            return original_name
        
        counter = 1
        while True:
            if policy == ConflictPolicy.KEEP_BOTH:
                import time
                new_name = ConflictResolver._generate_keep_both_name(original_name)
            else:
                new_name = ConflictResolver._generate_rename(original_name, counter)
            
            if new_name not in existing_names:
                return new_name
            
            counter += 1
            if counter > 10000:  # Safety limit
                raise ValueError("Could not find available name after 10000 attempts")
