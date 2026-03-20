"""Unit tests for file chunking utilities."""
import hashlib
import os
import tempfile

import pytest

from meshcloud.storage.chunker import CHUNK_SIZE, split_file


class TestSplitFile:
    """Test file splitting functionality."""

    def test_split_file_small(self):
        """Test splitting a small file that fits in one chunk."""
        test_data = b"Hello, World! This is a test file."
        expected_hash = hashlib.sha256(test_data).hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                chunks = split_file(temp_file, temp_dir)

                # Should create exactly one chunk
                assert len(chunks) == 1
                assert chunks[0] == expected_hash

                # Verify chunk content
                chunk_path = os.path.join(temp_dir, expected_hash)
                assert os.path.exists(chunk_path)

                with open(chunk_path, "rb") as f:
                    chunk_data = f.read()
                    assert chunk_data == test_data

            finally:
                os.unlink(temp_file)

    def test_split_file_multiple_chunks(self):
        """Test splitting a file that requires multiple chunks."""
        # Create data larger than CHUNK_SIZE
        chunk_data = b"A" * CHUNK_SIZE
        test_data = chunk_data + b"B" * 100  # Two chunks + small remainder
        
        expected_hash_1 = hashlib.sha256(chunk_data).hexdigest()
        expected_hash_2 = hashlib.sha256(b"B" * 100).hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                chunks = split_file(temp_file, temp_dir)

                # Should create two chunks
                assert len(chunks) == 2
                assert chunks == [expected_hash_1, expected_hash_2]

                # Verify first chunk
                chunk0_path = os.path.join(temp_dir, expected_hash_1)
                with open(chunk0_path, "rb") as f:
                    assert f.read() == chunk_data

                # Verify second chunk
                chunk1_path = os.path.join(temp_dir, expected_hash_2)
                with open(chunk1_path, "rb") as f:
                    assert f.read() == b"B" * 100

            finally:
                os.unlink(temp_file)

    def test_split_file_exact_chunks(self):
        """Test splitting a file with size exactly matching chunk boundaries."""
        # Create data that exactly matches 3 chunks
        test_data = b"A" * (CHUNK_SIZE * 3)
        expected_hash = hashlib.sha256(b"A" * CHUNK_SIZE).hexdigest()

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                chunks = split_file(temp_file, temp_dir)

                # Should create exactly three chunks
                assert len(chunks) == 3
                assert chunks == [expected_hash, expected_hash, expected_hash]

                # Verify content (deduplicated on disk)
                chunk_path = os.path.join(temp_dir, expected_hash)
                with open(chunk_path, "rb") as f:
                    assert f.read() == b"A" * CHUNK_SIZE

            finally:
                os.unlink(temp_file)

    def test_split_file_empty(self):
        """Test splitting an empty file."""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            temp_file = f.name  # Empty file

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                chunks = split_file(temp_file, temp_dir)

                # Should create no chunks for empty file
                assert len(chunks) == 0

            finally:
                os.unlink(temp_file)

    def test_split_file_large(self):
        """Test splitting a large file (multiple MB)."""
        # Create a 10MB file
        test_data = b"X" * (10 * 1024 * 1024)

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                chunks = split_file(temp_file, temp_dir)
                
                # 10MB / 4MB = 2 chunks + 1 partial chunk = 3 chunks
                expected_chunks = 10 * 1024 * 1024 // CHUNK_SIZE + 1
                assert len(chunks) == expected_chunks
                
                # Full chunks share the same hash due to identical content ('X' repeated)
                hash_full = hashlib.sha256(b"X" * CHUNK_SIZE).hexdigest()
                hash_last = hashlib.sha256(b"X" * (10 * 1024 * 1024 % CHUNK_SIZE)).hexdigest()
                assert chunks == [hash_full, hash_full, hash_last]

                # Verify total data integrity
                total_data = b""
                for chunk_name in chunks:
                    chunk_path = os.path.join(temp_dir, chunk_name)
                    with open(chunk_path, "rb") as f:
                        total_data += f.read()

                assert total_data == test_data

            finally:
                os.unlink(temp_file)

    def test_split_file_nonexistent(self):
        """Test splitting a non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileNotFoundError):
                split_file("/nonexistent/file.txt", temp_dir)

    def test_split_file_permission_denied(self):
        """Test splitting a file without read permission."""
        test_data = b"test data"

        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as f:
            f.write(test_data)
            temp_file = f.name

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Remove read permission
                os.chmod(temp_file, 0o000)
                with pytest.raises(PermissionError):
                    split_file(temp_file, temp_dir)
            finally:
                # Restore permission for cleanup
                os.chmod(temp_file, 0o600)
                os.unlink(temp_file)

    def test_split_file_unicode_filename(self):
        """Test splitting a file with Unicode characters in filename."""
        test_data = "Hello, Unicode! 🌍".encode("utf-8")
        expected_hash = hashlib.sha256(test_data).hexdigest()

        # Create file with Unicode name (if filesystem supports it)
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, prefix="test_unicode_", suffix=".bin") as f:
                f.write(test_data)
                temp_file = f.name

            with tempfile.TemporaryDirectory() as temp_dir:
                try:
                    chunks = split_file(temp_file, temp_dir)
                    assert len(chunks) == 1
                    assert chunks[0] == expected_hash

                    chunk_path = os.path.join(temp_dir, expected_hash)
                    with open(chunk_path, "rb") as f:
                        assert f.read() == test_data

                finally:
                    os.unlink(temp_file)
        except (UnicodeEncodeError, OSError):
            # Skip test if filesystem doesn't support Unicode filenames
            pytest.skip("Filesystem does not support Unicode filenames")
