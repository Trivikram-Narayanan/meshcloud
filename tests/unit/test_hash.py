"""Unit tests for hash utilities."""
import hashlib
import tempfile

import pytest

from meshcloud.storage.hash import sha256_file


class TestSHA256File:
    """Test SHA256 file hashing functionality."""

    def test_sha256_file_small(self):
        """Test SHA256 hashing of a small file."""
        test_data = b"Hello, World!"
        expected_hash = hashlib.sha256(test_data).hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        try:
            result = sha256_file(temp_file)
            assert result == expected_hash
            assert len(result) == 64  # SHA256 produces 64 character hex string
            assert result.isalnum()  # Should only contain alphanumeric characters
        finally:
            import os

            os.unlink(temp_file)

    def test_sha256_file_large(self):
        """Test SHA256 hashing of a larger file."""
        # Create a 1MB test file
        test_data = b"A" * (1024 * 1024)  # 1MB of 'A' characters
        expected_hash = hashlib.sha256(test_data).hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        try:
            result = sha256_file(temp_file)
            assert result == expected_hash
            assert len(result) == 64
        finally:
            import os

            os.unlink(temp_file)

    def test_sha256_file_empty(self):
        """Test SHA256 hashing of an empty file."""
        expected_hash = hashlib.sha256(b"").hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            temp_file = f.name  # Empty file

        try:
            result = sha256_file(temp_file)
            assert result == expected_hash
            assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        finally:
            import os

            os.unlink(temp_file)

    def test_sha256_file_unicode_content(self):
        """Test SHA256 hashing with Unicode content."""
        test_data = "Hello, 世界! 🌍".encode("utf-8")
        expected_hash = hashlib.sha256(test_data).hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        try:
            result = sha256_file(temp_file)
            assert result == expected_hash
        finally:
            import os

            os.unlink(temp_file)

    def test_sha256_file_nonexistent(self):
        """Test SHA256 hashing of non-existent file."""
        with pytest.raises(FileNotFoundError):
            sha256_file("/nonexistent/file.txt")

    def test_sha256_file_permission_denied(self):
        """Test SHA256 hashing when file permission is denied."""
        import os
        import stat

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(b"test data")
            temp_file = f.name

        try:
            # Remove read permission
            os.chmod(temp_file, 0o000)
            with pytest.raises(PermissionError):
                sha256_file(temp_file)
        finally:
            # Restore permission for cleanup
            os.chmod(temp_file, 0o600)
            os.unlink(temp_file)
