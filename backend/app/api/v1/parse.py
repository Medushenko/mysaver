"""
Parse API endpoint - POST /api/v1/parse
"""
from fastapi import APIRouter, HTTPException
from typing import List

from app.schemas.parse import ParseRequest, ParseResponse, LinkInfoSchema
from app.core.parsers import YandexLinkParser, GoogleLinkParser, LocalPathParser
from app.core.parsers.base import LinkInfo

router = APIRouter()


@router.post("/parse", response_model=ParseResponse)
async def parse_links(request: ParseRequest):
    """
    Parse text and extract links from various providers
    
    Accepts text containing URLs from:
    - Yandex Disk (yadi.sk, disk.yandex.ru/com)
    - Google Drive (drive.google.com)
    - Local file paths (Unix/Windows)
    
    Returns list of extracted links with provider and type information.
    """
    errors: List[str] = []
    links: List[LinkInfo] = []
    
    try:
        # Parse Yandex links
        yandex_parser = YandexLinkParser()
        yandex_links = yandex_parser.parse(request.text)
        links.extend(yandex_links)
    except Exception as e:
        errors.append(f"Yandex parser error: {str(e)}")
    
    try:
        # Parse Google Drive links
        google_parser = GoogleLinkParser()
        google_links = google_parser.parse(request.text)
        links.extend(google_links)
    except Exception as e:
        errors.append(f"Google parser error: {str(e)}")
    
    try:
        # Parse local paths
        local_parser = LocalPathParser()
        local_links = local_parser.parse(request.text)
        links.extend(local_links)
    except Exception as e:
        errors.append(f"Local parser error: {str(e)}")
    
    # Convert LinkInfo objects to schemas
    link_schemas = [
        LinkInfoSchema(
            url=link.url,
            provider=link.provider,
            type=link.type,
            metadata=link.metadata
        )
        for link in links
    ]
    
    return ParseResponse(links=link_schemas, errors=errors)
