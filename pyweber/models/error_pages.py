from pyweber.core.template import Template
from pyweber.utils.loads import StaticTemplates
from pyweber.utils.exceptions import InvalidTemplateError

class ErrorPages: # pragma: no cover
    def __init__(self):
        self.page_not_found = Template(template=StaticTemplates.PAGE_NOT_FOUND(), status_code=404)
        self.page_server_error = Template(template=StaticTemplates.PAGE_SERVER_ERROR(), status_code=500)
        self.page_unauthorized = Template(template=StaticTemplates.PAGE_UNAUTHORIZED(), status_code=401)
        
    @property
    def page_not_found(self) -> Template: return self.__page_not_found
    
    @page_not_found.setter
    def page_not_found(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()
        
        self.__page_not_found = template
    
    @property
    def page_unauthorized(self) -> Template: return self.__page_unauthorized

    @page_unauthorized.setter
    def page_unauthorized(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()
        
        self.__page_unauthorized = template
    
    @property
    def page_server_error(self) -> Template: return self.__page_server_error
    
    @page_server_error.setter
    def page_server_error(self, template: Template):
        if not isinstance(template, Template):
            raise InvalidTemplateError()
        
        self.__page_server_error = template