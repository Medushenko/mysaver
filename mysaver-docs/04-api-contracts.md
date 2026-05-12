
---

# 📁 `mysaver-docs/04-api-contracts.md`

```markdown
# 🔌 4. API контракты и адаптеры

## 🧩 StorageAdapter Interface
```python
class StorageAdapter:
    async def authenticate(self, oauth_token: str) -> bool: ...
    async def resolve_url(self, url: str) -> dict: ...  # type: file/folder, id, path
    async def list_folder(self, path: str) -> list[dict]: ...
    async def get_quota(self) -> dict: ...  # total, used, free
    async def copy(self, src: str, dst: str, opts: dict) -> str: ...  # job_id
    async def verify(self, job_id: str) -> dict: ...  # checksum/size match