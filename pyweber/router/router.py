from pyweber.core.template import Template
from pyweber.utils.load import StaticTemplates

class Router:
    def __init__(self):
        self.__routes: dict[str, Template] = {}
        self.__redirects: dict[str, str] = {}
        self.__page_not_found = Template(template=StaticTemplates.PAGE_NOT_FOUND())
    
    @property
    def list_routes(self) -> list[str]:
        return list(self.__routes.keys())
    
    @property
    def clear_routes(self) -> None:
        self.__routes.clear()
    
    @property
    def page_not_found(self):
        return self.__page_not_found
    
    @page_not_found.setter
    def page_not_found(self, template: Template):
        if not isinstance(template, Template):
            raise TypeError('O template deve ser da classe Template')

        self.__page_not_found = template
    
    def add_route(self, route: str, template: Template) -> None:

        if not route.startswith('/'):
            raise ValueError("A routa deve começar com o parâmetro /")
        
        elif route in self.__routes:
            raise ValueError(f"A routa {route} já existe, use update_route para editar")
        
        elif not isinstance(template, Template):
            raise TypeError("O template deve ser da classe Template")
        
        self.__routes[route] = template
    
    def update_route(self, route: str, template: Template) -> None:
        if route not in self.__routes:
            raise ValueError(f"A routa {route} ainda não existe, use add_route para criar")

        elif not isinstance(template, Template):
            raise TypeError("O template deve ser da classe Template")

        self.__routes[route] = template

    def remove_route(self, route: str) -> None:
        if route not in self.__routes:
            raise ValueError(f"A routa {route} não existe")

        del self.__routes[route]
    
    def redirect(self, from_route: str, to_route: str) -> str:
        if to_route not in self.__routes:
            raise ValueError(f"A routa {to_route} não existe, use add_route para criar")
        
        self.__redirects[from_route] = to_route
    
    def get_route(self, route: str) -> Template:
        if route in self.__redirects:
            route = self.__redirects[route]
        
        if route not in self.__routes:
            return self.__page_not_found
        
        return self.__routes[route]
    
    def get_redirected_route(self, route: str) -> str:
        return self.__redirects[route]
    
    def exists(self, route: str) -> bool:
        return route in self.__routes
    
    def is_redirected(self, route: str) -> bool:
        return route in self.__redirects