from pyweber.core.element import Element
from pyweber.components.input import Input
from typing import Callable, Literal

class Form(Element):
    def __init__(
        self,
        id: str = None,
        classes: list[str] = None,
        style: dict[str, str] = None,
        method: Literal['dialog', 'GET', 'POST'] = 'dialog',
        name: str = None,
        action: str = None,
        onclick: Callable = None,
        onsubmit: Callable = None,
        onreset: Callable = None,
        childs: list[Input] = None,
        autocomplete: str = None,
        target: str = None,
        enctype: Literal['text/plain', 'multipart/form-data', 'application/x-www-form-urlencoded'] = 'application/x-www-form-urlencoded',
        accept_charset: None = None,
        rel: str = None,
        tabindex: int = None,
        novalidate: bool = True,
        autocapitalize: bool = False,
        spellcheck: bool = False,
        **kwargs
    ):
        super().__init__(tag='form', classes=classes, style=style, id=id, childs=childs, **kwargs)
        self.method = method
        self.name = name
        self.action = action
        self.autocomplete = autocomplete
        self.target = target
        self.enctype = enctype
        self.accept_charset = accept_charset
        self.rel = rel
        self.tabindex = tabindex
        self.novalidate = novalidate
        self.autocapitalize = autocapitalize
        self.spellcheck = spellcheck
        self.onclick = onclick
        self.onsubmit = onsubmit
        self.onreset = onreset
        self.attrs = {}
    
    @property
    def onclick(self):
        return self.events.__dict__.get('onclick', None)
    
    @onclick.setter
    def onclick(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onclick', value)
    
    @property
    def onsubmit(self):
        return self.events.__dict__.get('onsubmit', None)

    @onsubmit.setter
    def onsubmit(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onsubmit', value)
    
    @property
    def onreset(self):
        return self.events.__dict__.get('onreset', None)

    @onreset.setter
    def onreset(self, value):
        if value and callable(value):
            setattr(self.events, 'onreset', value)
    
    @property
    def attrs(self):
        return self.__attrs
    
    @attrs.setter
    def attrs(self, value: dict[str, str]):
        if value:
            raise AttributeError('Subscript not allowed to this attribute')
        
        self.__attrs = {}
        for key, value in self.__dict__.items():
            if key in ['method', 'name', 'action', 'autocomplete', 'spellcheck', 'autocapitalize', 'novalidate', 'target', 'enctype', 'accept_charset', 'rel', 'tabindex'] and value:
                if key in ['autocomplete', 'spellcheck', 'autocapitalize', 'novalidate'] and value == True:
                    self.__attrs[key] = ''
                else:
                    if key == 'accept_charset':
                        self.__attrs['accept-charset'] = value
                    else:
                        self.__attrs[key] = value