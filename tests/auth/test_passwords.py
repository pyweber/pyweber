"""Password hashing tests."""

import pytest

from pyweber.auth.passwords import check_password, hash_password


def test_hash_and_check_roundtrip():
    encoded = hash_password('s3cret!')
    assert encoded.startswith('pbkdf2_sha256$')
    assert check_password('s3cret!', encoded)
    assert not check_password('wrong', encoded)


def test_empty_password_rejected():
    with pytest.raises(ValueError):
        hash_password('')


def test_tampered_hash_fails():
    encoded = hash_password('ok')
    parts = encoded.split('$')
    parts[-1] = '00' * 32
    assert not check_password('ok', '$'.join(parts))
