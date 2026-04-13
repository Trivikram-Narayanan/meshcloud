"""MeshCloud Python Client Library.

A Python client for interacting with MeshCloud distributed file storage systems.
"""

__version__ = "0.1.0"
__author__ = "MeshCloud Contributors"
__license__ = "Apache 2.0"

from .client import MeshCloudClient
from .exceptions import (
    APIError,
    AuthenticationError,
    DownloadError,
    MeshCloudError,
    RateLimitError,
    UploadError,
)

__all__ = [
    "MeshCloudClient",
    "MeshCloudError",
    "AuthenticationError",
    "UploadError",
    "DownloadError",
    "APIError",
    "RateLimitError",
]
