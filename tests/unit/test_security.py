import pytest

from app.core.errors import NotAuthenticatedError
from app.core.security import create_access_token, decode_access_token


def test_create_and_decode_access_token():
    token = create_access_token(subject="42")
    subject = decode_access_token(token)
    assert subject == "42"


def test_decode_invalid_token_raises_not_authenticated():
    with pytest.raises(NotAuthenticatedError):
        decode_access_token("token.invalide.xxx")


def test_expired_token_raises_not_authenticated():
    token = create_access_token(subject="1", expires_minutes=-1)
    with pytest.raises(NotAuthenticatedError):
        decode_access_token(token)
