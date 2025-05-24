from datetime import datetime, timezone, timedelta

class CookieManager:
    def __init__(self):
        self.__cookies: list[str] = []
    
    @property
    def cookies(self):
        return self.__cookies
    
    def set_cookie(
        self,
        cookie_name: str,
        cookie_value: str,
        path: str = '/',
        samesite: str = 'Strict',
        httponly: bool = True,
        secure: bool = True,
        expires_after_seconds: int = None,
        expires_after_hours: int = None,
        expires_after_days: int = None,
        max_age: int = None
    ):
        cookie = f'{cookie_name}={cookie_value}; Path={path};'

        if httponly:
            cookie += ' HttpOnly;'
        
        if secure:
            cookie += ' Secure;'
        
        if samesite:
            if samesite not in ['Strict', 'Lax']:
                raise ValueError("SameSite is not valid. Please use one of: ['Strict', 'Lax']")

            cookie += f' SameSite={str(samesite)}'

        expires_after_days = expires_after_days if isinstance(
            expires_after_days, (int, float)
        ) and expires_after_days > 0 else 0
        expires_after_hours = expires_after_hours if isinstance(
            expires_after_hours, (int, float)
        ) and expires_after_hours > 0 else 0
        expires_after_seconds = expires_after_seconds if isinstance(
            expires_after_seconds, (int, float)
        ) and expires_after_seconds > 0 else 0

        if expires_after_days>0 or expires_after_hours>0 or expires_after_seconds>0:
            expires = datetime.now(timezone.utc) + timedelta(
                days=expires_after_days,
                seconds=expires_after_seconds,
                hours=expires_after_hours
            )

            expires_str = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            cookie += f' Expires={expires_str};'
        
        if isinstance(max_age, (int, float)) and max_age > 0:
            cookie += f' Max-Age={max_age};'
        
        if cookie not in self.__cookies:
            self.__cookies.append(cookie)