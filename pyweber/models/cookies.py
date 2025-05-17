from datetime import datetime

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
        expires: datetime = None
    ):
        cookie = f'{cookie_name}={cookie_value}; Path={path};'

        if httponly:
            cookie += ' HttpOnly;'
        
        if secure:
            cookie += ' Secure;'
        
        if samesite not in ['Strict', 'Lax', None]:
            raise AttributeError('Samsite is not valid. Please use one of the options: [Strict, Lax, None]')
        
        if expires and not isinstance(expires, datetime):
            raise ArithmeticError('Datetime is not valid, please use datetime to define the expires date.')

        if expires:
            expires_str = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            cookie += f' Expires={expires_str};'
    
        cookie += f' SameSite={str(samesite)}'
        
        if cookie not in self.__cookies:
            self.__cookies.append(cookie)