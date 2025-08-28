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
    created_by : int

class VideoCreate(BaseModel):
    title: str
    description: str 
    file_path: str  
    created_by : int 
    


# class VideoUpdate(BaseModel):
#     title: str | None = None
#     description: str | None = None
#     file_path: str | None = None
#     status: str | None = None


