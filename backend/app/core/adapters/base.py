from abc import ABC, abstractmethod
from typing import Dict, Any

class StorageAdapterError(Exception):
    pass

class StorageAdapter(ABC):
    @abstractmethod
    async def authenticate(self, token: str) -> bool:
        pass

    @abstractmethod
    async def resolve_url(self, url: str) -> Dict:
        pass

    @abstractmethod
    async def copy(self, src: str, dst: str, opts: Dict) -> str:
        pass