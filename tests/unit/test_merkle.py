"""Unit tests for Merkle tree utilities."""
import hashlib

import pytest

from meshcloud.storage.merkle import build_merkle_tree, hash_pair


class TestHashPair:
    """Test hash pair functionality."""

    def test_hash_pair_basic(self):
        """Test basic hash pair functionality."""
        left = "hash1"
        right = "hash2"
        expected = hashlib.sha256((left + right).encode()).hexdigest()

        result = hash_pair(left, right)
        assert result == expected
        assert len(result) == 64  # SHA256 hex length

    def test_hash_pair_same_inputs(self):
        """Test hash pair with identical inputs."""
        value = "same_hash"
        expected = hashlib.sha256((value + value).encode()).hexdigest()

        result = hash_pair(value, value)
        assert result == expected

    def test_hash_pair_empty_strings(self):
        """Test hash pair with empty strings."""
        expected = hashlib.sha256(b"").hexdigest()

        result = hash_pair("", "")
        assert result == expected

    def test_hash_pair_unicode(self):
        """Test hash pair with Unicode strings."""
        left = "café"
        right = "naïve"
        expected = hashlib.sha256((left + right).encode()).hexdigest()

        result = hash_pair(left, right)
        assert result == expected


class TestBuildMerkleTree:
    """Test Merkle tree construction."""

    def test_build_merkle_tree_single_leaf(self):
        """Test Merkle tree with single leaf."""
        leaves = ["hash1"]
        result = build_merkle_tree(leaves)
        assert result == "hash1"

    def test_build_merkle_tree_two_leaves(self):
        """Test Merkle tree with two leaves."""
        leaves = ["hash1", "hash2"]
        expected = hash_pair("hash1", "hash2")

        result = build_merkle_tree(leaves)
        assert result == expected

    def test_build_merkle_tree_four_leaves(self):
        """Test Merkle tree with four leaves."""
        leaves = ["h1", "h2", "h3", "h4"]

        # Level 1
        h12 = hash_pair("h1", "h2")
        h34 = hash_pair("h3", "h4")

        # Level 2 (root)
        expected_root = hash_pair(h12, h34)

        result = build_merkle_tree(leaves)
        assert result == expected_root

    def test_build_merkle_tree_odd_number(self):
        """Test Merkle tree with odd number of leaves."""
        leaves = ["h1", "h2", "h3"]

        # h1 and h2 are paired, h3 is duplicated
        h12 = hash_pair("h1", "h2")
        h33 = hash_pair("h3", "h3")  # Odd leaf duplicated
        expected_root = hash_pair(h12, h33)

        result = build_merkle_tree(leaves)
        assert result == expected_root

    def test_build_merkle_tree_empty(self):
        """Test Merkle tree with empty list."""
        with pytest.raises(IndexError):
            build_merkle_tree([])

    def test_build_merkle_tree_large(self):
        """Test Merkle tree with many leaves."""
        # Create 16 leaves
        leaves = [f"hash_{i}" for i in range(16)]

        result = build_merkle_tree(leaves)

        # Should produce a valid hash
        assert len(result) == 64
        assert result.isalnum()

        # Verify it's deterministic
        result2 = build_merkle_tree(leaves)
        assert result == result2

    def test_build_merkle_tree_real_hashes(self):
        """Test Merkle tree with real SHA256 hashes."""
        # Simulate file chunks
        data_chunks = [b"chunk1", b"chunk2", b"chunk3", b"chunk4"]
        leaves = [hashlib.sha256(chunk).hexdigest() for chunk in data_chunks]

        result = build_merkle_tree(leaves)

        # Should produce a valid root hash
        assert len(result) == 64
        assert result.isalnum()

        # Changing any leaf should change the root
        modified_leaves = leaves.copy()
        modified_leaves[0] = hashlib.sha256(b"modified").hexdigest()
        modified_result = build_merkle_tree(modified_leaves)

        assert modified_result != result

    def test_build_merkle_tree_deterministic(self):
        """Test that Merkle tree construction is deterministic."""
        leaves = ["a", "b", "c", "d", "e"]

        result1 = build_merkle_tree(leaves)
        result2 = build_merkle_tree(leaves)
        result3 = build_merkle_tree(leaves[::-1])  # Reversed order

        assert result1 == result2
        assert result1 != result3  # Order matters

    def test_build_merkle_tree_long_inputs(self):
        """Test Merkle tree with very long hash inputs."""
        # Simulate real-world 64-character SHA256 hashes
        leaves = [
            "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "b613679a0814d9ec772f95d778c35fc5ff1697c493715653c6c712144292c5ad",
            "c74d859b81b10b7b06cb5d5a0f1aa2cca0704ba60b76b99178486830c315612",
            "d4e6cb82b8bcb7b4f6f3218ceb531db04c37efe9f654f53aee486997cde6236",
        ]

        result = build_merkle_tree(leaves)

        # Should handle long inputs correctly
        assert len(result) == 64
        assert result.isalnum()

    def test_build_merkle_tree_case_sensitivity(self):
        """Test that Merkle tree is case-sensitive."""
        leaves1 = ["hash1", "HASH1"]
        leaves2 = ["hash1", "hash1"]

        result1 = build_merkle_tree(leaves1)
        result2 = build_merkle_tree(leaves2)

        assert result1 != result2
