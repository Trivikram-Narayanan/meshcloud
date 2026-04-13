"""Main MeshCloud client implementation."""

import hashlib
import io
import time
from pathlib import Path
from typing import Dict, List, Union, BinaryIO, Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    AuthenticationError,
    UploadError,
    APIError,
    RateLimitError,
    ValidationError,
    ConnectionError,
    TimeoutError,
    FileNotFoundError,
    PermissionError,
)


class MeshCloudClient:
    """Client for interacting with MeshCloud API.

    Provides a high-level interface for file uploads, downloads, and management
    operations in a MeshCloud distributed storage network.

    Example:
        ```python
        client = MeshCloudClient("https://meshcloud.example.com")
        client.authenticate("username", "password")

        # Upload a file
        with open("large_file.dat", "rb") as f:
            result = client.upload_file(f, "large_file.dat")
            print(f"Uploaded with hash: {result['hash']}")

        # Check file existence
        exists = client.file_exists(result['hash'])
        print(f"File exists: {exists}")
        ```
    """

    def __init__(
        self,
        base_url: str,
        username: str = None,
        password: str = None,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True,
        chunk_size: int = 4 * 1024 * 1024,  # 4MB
    ):
        """Initialize MeshCloud client.

        Args:
            base_url: Base URL of the MeshCloud node
            username: Username for authentication (optional)
            password: Password for authentication (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            verify_ssl: Whether to verify SSL certificates
            chunk_size: Size of chunks for file uploads (bytes)
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.verify_ssl = verify_ssl

        # Authentication
        self._token = None
        self._token_expires = None

        # HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Auto-authenticate if credentials provided
        if username and password:
            self.authenticate(username, password)

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with the MeshCloud node.

        Args:
            username: Username for authentication
            password: Password for authentication

        Returns:
            Authentication response containing access token

        Raises:
            AuthenticationError: If authentication fails
        """
        auth_data = {"username": username, "password": password}

        try:
            response = self.session.post(
                urljoin(self.base_url, "/token"),
                data=auth_data,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
            response.raise_for_status()

            token_data = response.json()
            self._token = token_data["access_token"]
            self._token_expires = time.time() + (30 * 60)  # 30 minutes

            # Update session headers
            self.session.headers.update({"Authorization": f"Bearer {self._token}"})

            return token_data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("Invalid username or password")
            raise APIError(f"Authentication failed: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Connection failed: {str(e)}")

    def _ensure_authenticated(self):
        """Ensure client is authenticated and token is valid."""
        if not self._token:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        # Check if token is about to expire (within 5 minutes)
        if self._token_expires and time.time() > (self._token_expires - 300):
            if self.username and self.password:
                self.authenticate(self.username, self.password)
            else:
                raise AuthenticationError("Token expired and no credentials available for renewal")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an authenticated HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            Various MeshCloudError subclasses based on response
        """
        self._ensure_authenticated()

        url = urljoin(self.base_url, endpoint)
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify_ssl)

        try:
            response = self.session.request(method, url, **kwargs)
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Failed to connect to MeshCloud node")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def _handle_response(self, response: requests.Response) -> requests.Response:
        """Handle HTTP response and raise appropriate exceptions."""
        if response.status_code == 401:
            raise AuthenticationError("Authentication required or token expired")
        elif response.status_code == 403:
            raise PermissionError("Access denied")
        elif response.status_code == 404:
            raise FileNotFoundError("Resource not found")
        elif response.status_code == 413:
            raise ValidationError("File too large")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError("Rate limit exceeded", retry_after=int(retry_after) if retry_after else None)
        elif not response.ok:
            try:
                error_data = response.json()
                message = error_data.get("detail", error_data.get("error", "Unknown error"))
            except ValueError:
                message = response.text or "Unknown error"

            raise APIError(message, status_code=response.status_code)

        return response

    def get_status(self) -> Dict[str, Any]:
        """Get node status information.

        Returns:
            Dictionary containing node status
        """
        response = self._make_request("GET", "/")
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the node.

        Returns:
            Health status information
        """
        response = self._make_request("GET", "/health")
        return response.json()

    def file_exists(self, file_hash: str) -> bool:
        """Check if a file exists on the node.

        Args:
            file_hash: SHA256 hash of the file

        Returns:
            True if file exists, False otherwise
        """
        try:
            response = self._make_request("GET", f"/has_file/{file_hash}")
            return response.json().get("exists", False)
        except FileNotFoundError:
            return False

    def get_file_locations(self, file_hash: str) -> List[str]:
        """Get all nodes that have a copy of the file.

        Args:
            file_hash: SHA256 hash of the file

        Returns:
            List of node URLs that have the file
        """
        response = self._make_request("GET", f"/file_locations/{file_hash}")
        return response.json().get("nodes", [])

    def upload_file(
        self, file_obj: Union[str, Path, BinaryIO], filename: str = None, progress_callback: callable = None
    ) -> Dict[str, Any]:
        """Upload a file to MeshCloud.

        Args:
            file_obj: File path (str/Path) or file-like object
            filename: Optional filename (inferred from path if not provided)
            progress_callback: Optional callback function for upload progress

        Returns:
            Upload result with file hash and metadata
        """
        # Handle different input types
        if isinstance(file_obj, (str, Path)):
            path = Path(file_obj)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            filename = filename or path.name
            file_size = path.stat().st_size
            file_handle = open(path, "rb")
        else:
            # Assume it's a file-like object
            file_handle = file_obj
            if hasattr(file_obj, "name") and not filename:
                filename = Path(file_obj.name).name
            # Try to get size
            if hasattr(file_obj, "seek") and hasattr(file_obj, "tell"):
                current_pos = file_obj.tell()
                file_obj.seek(0, 2)  # Seek to end
                file_size = file_obj.tell()
                file_obj.seek(current_pos)  # Seek back
            else:
                file_size = None

        try:
            # For large files, use chunked upload
            if file_size and file_size > self.chunk_size:
                return self._upload_chunked(file_handle, filename, file_size, progress_callback)
            else:
                return self._upload_simple(file_handle, filename, file_size, progress_callback)

        finally:
            # Close file if we opened it
            if isinstance(file_obj, (str, Path)):
                file_handle.close()

    def _upload_simple(
        self, file_handle: BinaryIO, filename: str, file_size: int = None, progress_callback: callable = None
    ) -> Dict[str, Any]:
        """Upload a file in a single request."""
        # Use chunked upload logic even for small files for consistency
        return self._upload_chunked(file_handle, filename, file_size, progress_callback)

    def _upload_chunked(
        self, file_handle: BinaryIO, filename: str, file_size: int, progress_callback: callable = None
    ) -> Dict[str, Any]:
        """Upload a file using chunked upload."""
        # Calculate number of chunks
        num_chunks = (file_size + self.chunk_size - 1) // self.chunk_size

        # Start upload session
        start_data = {"filename": filename, "total_chunks": num_chunks}

        start_response = self._make_request("POST", "/start_upload", json=start_data)
        upload_id = start_response.json()["upload_id"]

        try:
            # Upload chunks
            chunks = []
            for chunk_index in range(num_chunks):
                # Read chunk
                chunk_data = file_handle.read(self.chunk_size)
                if not chunk_data:
                    break

                # Calculate chunk hash
                chunk_hash = hashlib.sha256(chunk_data).hexdigest()

                # Upload chunk
                files = {"file": ("chunk", io.BytesIO(chunk_data), "application/octet-stream")}
                data = {"upload_id": upload_id, "chunk_index": chunk_index, "chunk_hash": chunk_hash}

                self._make_request("POST", "/upload_chunk", files=files, data=data)
                chunks.append(chunk_hash)

                # Progress callback
                if progress_callback:
                    progress = (chunk_index + 1) / num_chunks * 100
                    progress_callback(progress, chunk_index + 1, num_chunks)

            # Finalize upload
            finalize_data = {"upload_id": upload_id, "chunks": chunks, "filename": filename}

            finalize_response = self._make_request("POST", "/finalize_upload", json=finalize_data)
            return finalize_response.json()

        except Exception as e:
            # TODO: Cleanup partial upload
            raise UploadError(f"Upload failed: {str(e)}")

    def get_upload_status(self, upload_id: str) -> Dict[str, Any]:
        """Get the status of an ongoing upload.

        Args:
            upload_id: Upload session ID

        Returns:
            Upload status information
        """
        response = self._make_request("GET", f"/upload_status/{upload_id}")
        return response.json()

    def get_metrics(self, metric_type: str = "application") -> Dict[str, Any]:
        """Get system or application metrics.

        Args:
            metric_type: Type of metrics ("system", "application", or "health")

        Returns:
            Metrics data
        """
        if metric_type == "health":
            response = self._make_request("GET", "/metrics/health/detailed")
        elif metric_type == "system":
            response = self._make_request("GET", "/metrics/system")
        else:  # application
            response = self._make_request("GET", "/metrics/application")

        return response.json()

    def get_recent_requests(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent API requests.

        Args:
            limit: Maximum number of requests to return

        Returns:
            Recent request data
        """
        response = self._make_request("GET", f"/metrics/requests/recent?limit={limit}")
        return response.json()

    def get_recent_errors(self, limit: int = 20) -> Dict[str, Any]:
        """Get recent API errors.

        Args:
            limit: Maximum number of errors to return

        Returns:
            Recent error data
        """
        response = self._make_request("GET", f"/metrics/errors/recent?limit={limit}")
        return response.json()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()
