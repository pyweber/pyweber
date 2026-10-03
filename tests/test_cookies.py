import pytest
from pyweber.models.cookies import CookieManager

@pytest.fixture
def cookies():
    return CookieManager()

def test_set_cookies(cookies):
    cookies.set_cookie(
        cookie_name='name',
        cookie_value='Alex',
        expires_after_days=1,
        expires_after_hours=1,
        expires_after_seconds=60,
        max_age=3600
    )

    assert "name=Alex" in cookies.cookies['name']

def test_set_cookie_attributes_are_separated(cookies):
    cookies.set_cookie(
        cookie_name='name',
        cookie_value='Alex',
        expires_after_hours=10,
        max_age=36000
    )

    attributes = [a.strip() for a in cookies.cookies['name'].split(';') if a.strip()]

    assert 'SameSite=Strict' in attributes
    assert 'Max-Age=36000' in attributes
    assert any(a.startswith('Expires=') for a in attributes)

def test_raise_attributeerror(cookies):
    with pytest.raises(ValueError, match=r"SameSite is not valid. Please use one of: \['Strict', 'Lax']"):
        raise cookies.set_cookie(cookie_name='name', cookie_value='Alex', samesite='Match')