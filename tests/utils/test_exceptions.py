import pytest
from pyweber.utils.exceptions import (
    RouteNotFoundError,
    RouteNameNotFoundError,
    GroupRouteNotFoundError,
    RouteAlreadyExistError,
    RouteNameAlreadyExistError,
    InvalidTemplateError,
    InvalidRouteFormatError,
    InvalidCallableError
)

def test_route_not_found_error():
    with pytest.raises(RouteNotFoundError, match=r"The route /home that you try to acess not exist"):
        raise RouteNotFoundError("/home")

def test_route_name_not_found_error():
    with pytest.raises(RouteNameNotFoundError, match=r"The name dashboard that you try to acess not exist"):
        raise RouteNameNotFoundError("dashboard")

def test_group_route_not_found_error():
    with pytest.raises(GroupRouteNotFoundError, match=r"The group admin that you want to update does not existe"):
        raise GroupRouteNotFoundError("admin")

def test_route_already_exist_error():
    with pytest.raises(RouteAlreadyExistError, match=r"The route /admin already exists in this group routes"):
        raise RouteAlreadyExistError("/admin")

def test_route_name_already_exist_error():
    with pytest.raises(RouteNameAlreadyExistError, match=r"The name login already exists"):
        raise RouteNameAlreadyExistError("login")

def test_invalid_template_error():
    with pytest.raises(InvalidTemplateError, match=r"The template must be an instance of the Template class"):
        raise InvalidTemplateError()

def test_invalid_route_format_error():
    with pytest.raises(InvalidRouteFormatError, match=r"The route must start with /"):
        raise InvalidRouteFormatError()

def test_invalid_callable_error():
    with pytest.raises(InvalidCallableError, match=r"The decorator function must be a callable function"):
        raise InvalidCallableError()