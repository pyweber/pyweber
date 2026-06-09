from pyweber.core.element import Element
from pyweber.utils.types import Icons
from typing import Union, Literal, Callable

class Icon(Element):
    def __init__(self, value: Union[Icons, str]):
        super().__init__(tag='i')
        self.classes.append(value.value if isinstance(value, Icons) else value)

class Style(Element):
    def __init__(self, href: str):
        super().__init__(tag='link', attrs={'rel': 'stylesheet', 'href': href})

class Script(Element):
    def __init__(self, src: str = None, type: str = None, content: str = None):
        super().__init__(tag='script', content=content)
        self.type = type
        self.src = src
        self.attrs = {}
    
    @property
    def attrs(self):
        return getattr(self, '__attrs', {})
    
    @attrs.setter
    def attrs(self, value: dict[str, str]):
        if value:
            raise AttributeError('Cannot modify attrs attribute directly')
        
        self.__attrs: dict[str, str] = {}

        for key, value in self.__dict__.items():
            if key in ['src', 'type'] and value:
                self.__attrs[key] = value

class Label(Element):
    def __init__(
        self,
        content: str = None,
        to: str = None,
        form: str = None,
        id: str = None,
        classes: list[str, str] = None,
        style: dict[str, str] = None,
        tabindex: int = None,
    ):
        super().__init__(tag='label', id=id, classes=classes, style=style, content=content)
        self.to = to
        self.form = form
        self.tabindex = tabindex
        self.attrs = {}
    
    @property
    def attrs(self):
        return self.__attrs
    
    @attrs.setter
    def attrs(self, value: dict[str, str]):
        if value:
            raise AttributeError('Attributte not allowed to change default value')
        
        self.__attrs = {}
        for key, value in self.__dict__.items():
            if key in ['to', 'form', 'tabindex'] and value:
                if key == 'to':
                    self.__attrs['for'] = value
                else:
                    self.__attrs[key] = value

class TextArea(Element):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        content: str = None,
        rows: int = None,
        cols: int = None,
        form: str = None,
        maxlength: int = None,
        minlength: int = None,
        placeholder: str = None,
        readonly: bool = None,
        disabled: bool = None,
        required: bool = None,
        autofocus: bool = None,
        wrap: Literal["soft", "hard"] = None,
        autocomplete: str = None,
        spellcheck: bool = None,
        tabindex: int = None,
        classes: list[str] = None,
        style: dict[str, str] = None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        onselect: Callable = None,
        sanitize: bool = False
    ):
        super().__init__(tag='textarea')
        self.sanitize = sanitize
        self.content = content
        self.name = name
        self.id = id
        self.rows = rows
        self.cols = cols
        self.form = form
        self.maxlength = maxlength
        self.minlength = minlength
        self.placeholder = placeholder
        self.readonly = readonly
        self.disabled = disabled
        self.required = required
        self.autofocus = autofocus
        self.wrap = wrap
        self.autocomplete = autocomplete
        self.spellcheck = spellcheck
        self.tabindex = tabindex
        self.classes = classes or []
        self.style = style or {}
        self.onfocus = onfocus
        self.onblur = onblur
        self.onchange = onchange
        self.oninput = oninput
        self.onclick = onclick
        self.onselect = onselect
        self.attrs = {}
    
    @property
    def onclick(self):
        return self.events.__dict__.get('onclick', None)
    
    @onclick.setter
    def onclick(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onclick', value)

    @property
    def onfocus(self):
        return self.events.__dict__.get('onfocus', None)
    
    @onfocus.setter
    def onfocus(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onfocus', value)
    
    @property
    def onblur(self):
        return self.events.__dict__.get('onblur', None)
    
    @onblur.setter
    def onblur(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onblur', value)
    
    @property
    def onchange(self):
        return self.events.__dict__.get('onchange', None)
    
    @onchange.setter
    def onchange(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onchange', value)
    
    @property
    def oninput(self):
        return self.events.__dict__.get('oninput', None)
    
    @oninput.setter
    def oninput(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'oninput', value)
    
    @property
    def onselect(self):
        return self.events.__dict__.get('onselect', None)
    
    @onselect.setter
    def onselect(self, value: Callable):
        if value and callable(value):
            setattr(self.events, 'onselect', value)
    
    @property
    def attrs(self):
        return self.__attrs
    
    @attrs.setter
    def attrs(self, value: dict[str, str]):
        if value:
            raise AttributeError('Cannot modify attrs attribute directly')
        
        self.__attrs: dict[str, str] = {}

        for key, value in self.__dict__.items():
            if key in ['name', 'rows', 'cols', 'form', 'maxlength', 'minlength', 
                      'placeholder', 'readonly', 'disabled', 'required', 'autofocus', 
                      'wrap', 'autocomplete', 'spellcheck', 'tabindex'] and value:
                if key in ['readonly', 'disabled', 'required', 'autofocus'] and value == True:
                    self.__attrs[key] = ''
                elif key == 'spellcheck':
                    self.__attrs[key] = 'true' if value else 'false'
                else:
                    self.__attrs[key] = str(value)