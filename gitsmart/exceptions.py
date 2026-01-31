"""
GitSmart Exceptions - Custom exception classes for better error handling
"""


class GitSmartError(Exception):
    """Base exception for GitSmart errors"""
    pass


class NotAGitRepoError(GitSmartError):
    """Raised when trying to operate outside a git repository"""
    pass


class APIKeyMissingError(GitSmartError):
    """Raised when AI provider API key is missing"""
    pass


class AIProviderError(GitSmartError):
    """Raised when AI provider encounters an error"""
    pass


class ConfigurationError(GitSmartError):
    """Raised when there's a configuration issue"""
    pass


class StorageError(GitSmartError):
    """Raised when there's a storage/filesystem issue"""
    pass