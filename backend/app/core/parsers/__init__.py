"""
Parsers package initialization
"""
from app.core.parsers.base import LinkParser, LinkInfo
from app.core.parsers.yandex import YandexLinkParser
from app.core.parsers.google import GoogleLinkParser
from app.core.parsers.local import LocalPathParser

__all__ = [
    'LinkParser',
    'LinkInfo',
    'YandexLinkParser',
    'GoogleLinkParser',
    'LocalPathParser',
]
