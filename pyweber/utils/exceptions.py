class RouterError(Exception):
    """Base exception for router errors."""
    pass

class RouteNotFoundError(RouterError):
    def __init__(self, route: str):
        super().__init__(f'The route {route} that you try to acess not exist. Use add_route to create it')

class GroupRouteNotFoundError(RouterError):
    def __init__(self, group: str):
        super().__init__(f'The group {group} that you want to update does not existe. Please, create it before')

class RouteAlreadyExistError(RouterError):
    def __init__(self, route: str):
        super().__init__(f'The route {route} already exists in this group routes. Use update_route to edit it.')

class InvalidTemplateError(RouterError):
    """Exception for invalid template."""
    def __init__(self):
        super().__init__("The template must be an instance of the Template class.")

class InvalidRouteFormatError(RouterError):
    """Exception for invalid route format."""
    def __init__(self):
        super().__init__("The route must start with /")

class InvalidCallableError(RouterError):
    """Exception for invalid callable format"""
    def __init__(self):
        super().__init__("The decorator function must be a callable function")