from app.utils.hashing import hash_password, verify_password


def test_hash_password_is_not_plaintext():
    hashed = hash_password("MonMotDePasse123")
    assert hashed != "MonMotDePasse123"


def test_verify_password_success():
    hashed = hash_password("MonMotDePasse123")
    assert verify_password("MonMotDePasse123", hashed) is True


def test_verify_password_failure():
    hashed = hash_password("MonMotDePasse123")
    assert verify_password("MauvaisMotDePasse", hashed) is False
