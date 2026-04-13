"""Exception classes for MeshCloud client library."""


class MeshCloudError(Exception):
    """Base exception for MeshCloud client errors."""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}

    def __str__(self):
        if self.status_code:
            return f"{self.status_code}: {self.message}"
        return self.message


class AuthenticationError(MeshCloudError):
    """Raised when authentication fails."""

    pass


class UploadError(MeshCloudError):
    """Raised when file upload fails."""

    pass


class DownloadError(MeshCloudError):
    """Raised when file download fails."""

    pass


class APIError(MeshCloudError):
    """Raised when API request fails."""

    pass


class RateLimitError(MeshCloudError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

    def __str__(self):
        if self.retry_after:
            return f"{super().__str__()} (retry after {self.retry_after} seconds)"
        return super().__str__()


class ValidationError(MeshCloudError):
    """Raised when input validation fails."""

    pass


class ConnectionError(MeshCloudError):
    """Raised when connection to server fails."""

    pass


class TimeoutError(MeshCloudError):
    """Raised when request times out."""

    pass


class FileNotFoundError(MeshCloudError):
    """Raised when requested file is not found."""

    pass


class PermissionError(MeshCloudError):
    """Raised when access is denied."""

    pass
