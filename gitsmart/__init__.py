"""
GitSmart: Your git repository's memory made searchable
"""

__version__ = "0.1.0"
__author__ = "GitSmart Team"
__email__ = "support@gitsmart.dev"

from .git_context import GitContextExtractor
from .ai_provider import AIProvider, OpenAIProvider
from .storage import KnowledgeStorage

__all__ = [
    "GitContextExtractor",
    "AIProvider", 
    "OpenAIProvider",
    "KnowledgeStorage",
]