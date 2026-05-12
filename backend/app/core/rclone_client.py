import httpx
from typing import Dict, Any
from app.config import settings

class RcloneClient:
    def __init__(self):
        self.base_url = settings.RCLONE_RC_ADDR
        self.client = httpx.AsyncClient(timeout=30.0)

    async def rc_call(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self.client.post(url, json=params or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": str(e), "status": e.response.status_code}
        except Exception as e:
            return {"error": str(e)}

    async def start_copy(self, src_fs: str, dst_fs: str, opts: dict = None) -> str:
        params = {
            "srcFs": src_fs,
            "dstFs": dst_fs,
            "_async": True,
            **(opts or {})
        }
        result = await self.rc_call("sync/copy", params)
        return result.get("jobid", "unknown")

    async def get_job_status(self, job_id: str) -> Dict:
        return await self.rc_call("job/status", {"jobid": job_id})