class ResearchProviderError(Exception):
    """Base exception for research metadata providers."""
    def __init__(self, message: str, provider: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status_code = status_code


class ProviderNotConfiguredException(ResearchProviderError):
    """Raised when an external provider requires API keys that are not configured."""
    def __init__(self, message: str, provider: str):
        super().__init__(message=message, provider=provider, status_code=503)


class ProviderRateLimitError(ResearchProviderError):
    """Raised when an external provider rate limits requests."""
    def __init__(self, message: str, provider: str):
        super().__init__(message=message, provider=provider, status_code=429)


class ProviderTimeoutError(ResearchProviderError):
    """Raised when an external provider request times out."""
    def __init__(self, message: str, provider: str):
        super().__init__(message=message, provider=provider, status_code=504)
