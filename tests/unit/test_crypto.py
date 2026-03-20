import os

import pytest

from meshcloud.security.crypto import decrypt_data, encrypt_data


class TestCrypto:
    def test_encryption_decryption_cycle(self):
        """Test that data can be encrypted and then decrypted back to the original."""
        original_data = b"This is a secret message for testing."

        encrypted_data = encrypt_data(original_data)

        # Ciphertext should not be the same as plaintext
        assert encrypted_data != original_data

        decrypted_data = decrypt_data(encrypted_data)

        # Decrypted data should match the original
        assert decrypted_data == original_data

    def test_decryption_failure_with_invalid_token(self):
        """Test that decryption fails with invalid or corrupted data."""
        invalid_token = b"gAAAAABm_...this_is_not_a_valid_token"

        with pytest.raises(Exception):
            decrypt_data(invalid_token)

    def test_decryption_failure_with_tampered_data(self):
        """Test that decryption fails if the encrypted data is tampered with."""
        original_data = b"This is some important data."
        encrypted_data = encrypt_data(original_data)

        # Tamper with the encrypted data (e.g., flip a byte)
        tampered_data = encrypted_data[:-1] + bytes([encrypted_data[-1] ^ 1])

        with pytest.raises(Exception):
            decrypt_data(tampered_data)

    def test_key_derivation_from_env_var(self):
        """Test that the encryption key is derived from the environment variable."""
        with pytest.MonkeyPatch.context() as m:
            m.setenv("STORAGE_ENCRYPTION_KEY", "key1")
            encrypted1 = encrypt_data(b"data")
            m.setenv("STORAGE_ENCRYPTION_KEY", "key2")
            encrypted2 = encrypt_data(b"data")
            assert encrypted1 != encrypted2