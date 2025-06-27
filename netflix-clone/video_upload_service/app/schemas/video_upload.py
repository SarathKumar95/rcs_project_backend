from pydantic import BaseModel

class UploadChunkRequest(BaseModel):
    upload_id: str
    chunk_index: int