from app.core.adapters.base import StorageAdapter

class YandexDiskAdapter(StorageAdapter):
    async def authenticate(self, token: str) -> bool:
        return True  # заглушка
    
    async def resolve_url(self, url: str) -> dict:
        return {"type": "folder", "id": "yandex:" + url, "path": url}
    
    async def copy(self, src: str, dst: str, opts: dict) -> str:
        return "yandex-copy-job"  # заглушка