"""
Schemas for parse API endpoints
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class LinkInfoSchema(BaseModel):
    """Schema for link information"""
    url: str
    provider: str  # yandex|google|local
    type: str  # file|folder
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class ParseRequest(BaseModel):
    """Request schema for parsing text"""
    text: str = Field(..., min_length=1, description="Text containing links to parse")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Check these links:\nhttps://yadi.sk/d/abc123\nhttps://drive.google.com/file/d/xyz789"
            }
        }


class ParseResponse(BaseModel):
    """Response schema for parse endpoint"""
    links: List[LinkInfoSchema]
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "links": [
                    {
                        "url": "https://yadi.sk/d/abc123",
                        "provider": "yandex",
                        "type": "file",
                        "metadata": {"parsed_by": "YandexLinkParser"}
                    }
                ],
                "errors": []
            }
        }
