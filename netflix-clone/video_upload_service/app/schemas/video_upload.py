from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


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
    model_config = ConfigDict(str_strip_whitespace=True)
    key: str
    upload_id: str
    parts: List[Part]
    created_by : int
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(max_length=2000)

class VideoCreate(BaseModel):
    title: str
    description: str 
    file_path: str  
    created_by : int 
    

class Post_Transcode_Update(BaseModel):
    hls_path: Optional[str] = None
    upload_status: Optional[int] = None
    resolutions: Optional[Dict[str, str]] = None
    
    class Config:
        orm_mode = True


class Update_Video_Record(BaseModel):
    video_id: str
    # title: Optional[str] = None 
    # description: Optional[str] = None 
    hls_path: Optional[str] = None
    upload_status: Optional[int] = None 
    # resolutions: Optional[Dict[str, str]] = None 

    class Config:
        orm_mode = True