from app.core.adapters.base import StorageAdapter

class GoogleDriveAdapter(StorageAdapter):
    async def authenticate(self, token: str) -> bool:
        return True
    
    async def resolve_url(self, url: str) -> dict:
        return {"type": "folder", "id": "google:" + url, "path": url}
    
    async def copy(self, src: str, dst: str, opts: dict) -> str:
        return "google-copy-job"