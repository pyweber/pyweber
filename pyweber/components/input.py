from pyweber.core.element import Element
from typing import Callable, Literal

class Input(Element):
    def __init__(
        self,
        type: str,
        name: str,
        id: str,
        form: str,
        tabindex: int,
        classes: list[str],
        style: dict[str, str],
        disabled: bool,
        autofocus: bool,
        required: bool,
        onfocus: Callable,
        onblur: Callable,
        onchange: Callable,
        oninput: Callable,
        onclick: Callable,
    ):
        super().__init__(tag='input')
        self.type = type
        self.style = style or {}
        self.id = id
        self.classes = classes or []
        self.name = name
        self.form = form
        self.tabindex = tabindex
        self.disabled = disabled
        self.autofocus = autofocus
        self.required = required
        self.onfocus = onfocus
        self.onblur = onblur
        self.onchange = onchange
        self.oninput = oninput
        self.onclick = onclick
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
    def attrs(self):
        return self.__attrs
    
    @attrs.setter
    def attrs(self, value: dict[str, str]):
        if value:
            raise AttributeError('Cannot modify attrs attribute directly')
        
        self.__attrs: dict[str, str] = {}

        for key, value in self.__dict__.items():
            if key in ['type', 'form', 'name', 'tabindex', 'autofocus', 'required', 'disabled'] and value:
                if key in ['disabled', 'autofocus', 'required']:
                    if getattr(self, key) == True:
                        self.__attrs[key] = ''
                else:
                    self.__attrs[key] = value

class InputColor(Input):
    def __init__(self,
        name: str = None,
        id: str = None,
        value: str = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        onfocus = None,
        onblur = None,
        onchange = None,
        oninput = None,
        onclick = None,
    ):
        super().__init__('color', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value

class InputText(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: str = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus = None,
        onblur = None,
        onchange = None,
        oninput = None,
        onclick = None,
    ):
        super().__init__('text', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly'] and value:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value

class InputPassword(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: Literal['current-password', 'new-password'] = "current-password",
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        showpassword: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('password', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        self.showpassword = showpassword
        self.__update_attributes
        self.__toogle_type
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly'] and value:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value
    
    @property
    def __toogle_type(self):
        if self.showpassword == True:
            self._Input__attrs['type'] = 'text'
        else:
            self._Input__attrs['type'] = 'password'


class InputEmail(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: str = "email",
        multiple: bool = False,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('email', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        self.multiple = multiple
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly', 'multiple'] and value:
                if key in ['readonly', 'multiple'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputNumber(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        min: int = None,
        max: int = None,
        step: int = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('number', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.min = min
        self.max = max
        self.step = step
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'min', 'max', 'step', 'readonly'] and value is not None:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputFile(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        accept: str = None,
        multiple: bool = False,
        capture: str = None,  # camera, microphone
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('file', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.accept = accept
        self.multiple = multiple
        self.capture = capture
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['accept', 'multiple', 'capture'] and value:
                if key in ['multiple'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputCheckbox(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = "on",
        checked: bool = False,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('checkbox', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.checked = checked
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['value', 'checked'] and value:
                if key in ['checked'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputRadio(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        checked: bool = False,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('radio', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.checked = checked
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['checked'] and value:
                if key in ['checked'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputRange(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        min: int = None,
        max: int = None,
        step: int = None,
        list: str = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('range', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.list = list
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['min', 'max', 'step', 'list'] and value is not None:
                self._Input__attrs[key] = value


class InputDate(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        min: str = None,  
        max: str = None,  
        step: int = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('date', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['min', 'max', 'step', 'readonly'] and value is not None:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputTime(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        min: str = None,  
        max: str = None,  
        step: int = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('time', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['min', 'max', 'step', 'readonly'] and value is not None:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputSearch(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: str = "off",
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('search', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly'] and value:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputTel(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: str = "tel",
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('tel', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly'] and value:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputUrl(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: str = "url",
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        required = False,
        readonly: bool = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('url', name, id, form, tabindex, classes, style, disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly'] and value:
                if key in ['readonly'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputHidden(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        form = None,
        classes = None,
        style = None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('hidden', name, id, form, None, classes, style, False, False, False, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value


class InputSubmit(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = "Submit",
        formaction: str = None,
        formmethod: Literal['POST', 'GET'] = None,
        formnovalidate: bool = False,
        formtarget: Literal['_blank', '_self', '_parent', '_top'] = None,
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('submit', name, id, form, tabindex, classes, style, disabled, autofocus, False, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value
        self.formaction = formaction
        self.formmethod = formmethod
        self.formnovalidate = formnovalidate
        self.formtarget = formtarget
        self.__update_attributes
    
    @property
    def __update_attributes(self):
        for key, value in self.__dict__.items():
            if key in ['formaction', 'formmethod', 'formnovalidate', 'formtarget'] and value:
                if key in ['formnovalidate'] and value == True:
                    self._Input__attrs[key] = ''
                else:
                    self._Input__attrs[key] = value


class InputButton(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = "Button",
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('button', name, id, form, tabindex, classes, style, disabled, autofocus, False, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value


class InputReset(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = "Reset",
        form = None,
        tabindex = None,
        classes = None,
        style = None,
        disabled = False,
        autofocus = False,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__('reset', name, id, form, tabindex, classes, style, disabled, autofocus, False, onfocus, onblur, onchange, oninput, onclick,)
        self.value = value