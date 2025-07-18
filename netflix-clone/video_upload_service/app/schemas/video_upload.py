from typing import List
from pydantic import BaseModel


class InitiateUploadRequest(BaseModel):
    filename: str


class GetUploadUrlRequest(BaseModel):
    key: str
    upload_id: str
    part_number: int


class Part(BaseModel):
    ETag: str
    PartNumber: int

class CompleteUploadRequest(BaseModel):
    key: str
    upload_id: str
    parts: List[Part]