"""HTML ``<input>`` components with a shared declarative attribute sync."""

from __future__ import annotations

from typing import Callable, Literal

from pyweber.core.element import Element

_COMMON_ATTR_KEYS = frozenset({
    'type', 'form', 'name', 'tabindex', 'autofocus', 'required', 'disabled',
})
_COMMON_BOOL_ATTRS = frozenset({'disabled', 'autofocus', 'required'})


class Input(Element):
    """Base input. Subclasses declare ``_EXTRA_ATTRS`` / ``_BOOLEAN_ATTRS``."""

    _EXTRA_ATTRS: frozenset[str] = frozenset()
    _BOOLEAN_ATTRS: frozenset[str] = frozenset(_COMMON_BOOL_ATTRS)
    _STRINGIFY_ATTRS: frozenset[str] = frozenset()

    def __init__(
        self,
        type: str,
        name: str = None,
        id: str = None,
        form: str = None,
        tabindex: int = None,
        classes: list[str] = None,
        style: dict[str, str] = None,
        disabled: bool = None,
        autofocus: bool = None,
        required: bool = None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        **kwargs,
    ):
        super().__init__(tag='input', **kwargs)
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

    def _attr_store(self) -> dict[str, str]:
        return self.__attrs

    def _sync_attrs(self):
        """Push declared extra attributes into the internal attrs dict."""
        store = self._attr_store()
        bool_attrs = self._BOOLEAN_ATTRS
        stringify = self._STRINGIFY_ATTRS
        for key in self._EXTRA_ATTRS:
            value = getattr(self, key, None)
            if value is None:
                continue
            if key in bool_attrs and value is True:
                store[key] = ''
            elif key in stringify:
                store[key] = str(value)
            else:
                store[key] = value

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

        for key, val in self.__dict__.items():
            if key in _COMMON_ATTR_KEYS and val:
                if key in _COMMON_BOOL_ATTRS:
                    if getattr(self, key) is True:
                        self.__attrs[key] = ''
                else:
                    self.__attrs[key] = val


class _TextualInput(Input):
    """Shared fields for text-like inputs (text, password, email, search, tel, url)."""

    _EXTRA_ATTRS = frozenset({
        'placeholder', 'autocomplete', 'size', 'maxlength', 'minlength', 'pattern', 'readonly',
    })
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'readonly'})

    def __init__(
        self,
        input_type: str,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        size: int = None,
        maxlength: int = None,
        minlength: int = None,
        pattern: str = None,
        autocomplete: str = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        readonly: bool = None,
        onfocus=None,
        onblur=None,
        onchange=None,
        oninput=None,
        onclick=None,
        sanitize: bool = True,
        **extra,
    ):
        super().__init__(
            input_type, name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value
        self.placeholder = placeholder
        self.size = size
        self.maxlength = maxlength
        self.minlength = minlength
        self.pattern = pattern
        self.autocomplete = autocomplete
        self.readonly = readonly
        for key, val in extra.items():
            setattr(self, key, val)
        self._sync_attrs()


class _DateTimeInput(Input):
    _EXTRA_ATTRS = frozenset({'min', 'max', 'step', 'readonly'})
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'readonly'})

    def __init__(
        self,
        input_type: str,
        name: str = None,
        id: str = None,
        value: str = None,
        min: str = None,
        max: str = None,
        step: int = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        readonly: bool = None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__(
            input_type, name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.readonly = readonly
        self._sync_attrs()


class InputColor(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        onfocus=None,
        onblur=None,
        onchange=None,
        oninput=None,
        onclick=None,
        sanitize: bool = True,
    ):
        super().__init__(
            'color', name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value


class InputText(_TextualInput):
    def __init__(self, name: str = None, id: str = None, value: str = None, **kwargs):
        super().__init__('text', name=name, id=id, value=value, **kwargs)


class InputPassword(_TextualInput):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        autocomplete: Literal['current-password', 'new-password'] = 'current-password',
        showpassword: bool = None,
        **kwargs,
    ):
        super().__init__(
            'password',
            name=name,
            id=id,
            value=value,
            autocomplete=autocomplete,
            showpassword=showpassword,
            **kwargs,
        )
        self.showpassword = showpassword
        store = self._attr_store()
        store['type'] = 'text' if showpassword is True else 'password'


class InputEmail(_TextualInput):
    _EXTRA_ATTRS = _TextualInput._EXTRA_ATTRS | frozenset({'multiple'})
    _BOOLEAN_ATTRS = _TextualInput._BOOLEAN_ATTRS | frozenset({'multiple'})

    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        autocomplete: str = 'email',
        multiple: bool = None,
        **kwargs,
    ):
        super().__init__(
            'email',
            name=name,
            id=id,
            value=value,
            autocomplete=autocomplete,
            multiple=multiple,
            **kwargs,
        )


class InputSearch(_TextualInput):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        autocomplete: str = 'off',
        **kwargs,
    ):
        super().__init__(
            'search', name=name, id=id, value=value, autocomplete=autocomplete, **kwargs,
        )


class InputTel(_TextualInput):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        autocomplete: str = 'tel',
        **kwargs,
    ):
        super().__init__(
            'tel', name=name, id=id, value=value, autocomplete=autocomplete, **kwargs,
        )


class InputUrl(_TextualInput):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        autocomplete: str = 'url',
        **kwargs,
    ):
        super().__init__(
            'url', name=name, id=id, value=value, autocomplete=autocomplete, **kwargs,
        )


class InputNumber(Input):
    _EXTRA_ATTRS = frozenset({'placeholder', 'min', 'max', 'step', 'readonly'})
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'readonly'})
    _STRINGIFY_ATTRS = frozenset({'placeholder', 'min', 'max', 'step', 'readonly'})

    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        placeholder: str = None,
        min: int = None,
        max: int = None,
        step: int = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        readonly: bool = None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        sanitize: bool = True,
    ):
        super().__init__(
            'number', name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value
        self.placeholder = placeholder
        self.min = min
        self.max = max
        self.step = step
        self.readonly = readonly
        self._sync_attrs()


class InputFile(Input):
    _EXTRA_ATTRS = frozenset({'accept', 'multiple', 'capture'})
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'multiple'})

    def __init__(
        self,
        name: str = None,
        id: str = None,
        accept: str = None,
        multiple: bool = None,
        capture: Literal['camera', 'microphone'] = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__(
            'file', name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.accept = accept
        self.multiple = multiple
        self.capture = capture
        self._sync_attrs()


class InputCheckbox(Input):
    _EXTRA_ATTRS = frozenset({'value', 'checked'})
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'checked'})

    def __init__(
        self,
        name: str,
        value: str,
        id: str = None,
        checked: bool = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__(
            'checkbox', name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.value = value
        self.checked = checked
        self._sync_attrs()


class InputRadio(Input):
    """Radio only syncs ``checked`` into attrs (``value`` stays on the instance)."""

    _EXTRA_ATTRS = frozenset({'checked'})
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'checked'})

    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        checked: bool = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__(
            'radio', name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.value = value
        self.checked = checked
        self._sync_attrs()


class InputRange(Input):
    _EXTRA_ATTRS = frozenset({'min', 'max', 'step', 'list'})

    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        min: int = None,
        max: int = None,
        step: int = None,
        list: str = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        required=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
    ):
        super().__init__(
            'range', name, id, form, tabindex, classes, style,
            disabled, autofocus, required, onfocus, onblur, onchange, oninput, onclick,
        )
        self.value = value
        self.min = min
        self.max = max
        self.step = step
        self.list = list
        self._sync_attrs()


class InputDate(_DateTimeInput):
    def __init__(self, name: str = None, id: str = None, value: str = None, **kwargs):
        super().__init__('date', name=name, id=id, value=value, **kwargs)


class InputTime(_DateTimeInput):
    def __init__(self, name: str = None, id: str = None, value: str = None, **kwargs):
        super().__init__('time', name=name, id=id, value=value, **kwargs)


class InputHidden(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = None,
        form=None,
        classes=None,
        style=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        sanitize: bool = True,
    ):
        super().__init__(
            'hidden', name, id, form, None, classes, style,
            None, None, None, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value


class InputSubmit(Input):
    _EXTRA_ATTRS = frozenset({'formaction', 'formmethod', 'formnovalidate', 'formtarget'})
    _BOOLEAN_ATTRS = Input._BOOLEAN_ATTRS | frozenset({'formnovalidate'})

    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = 'Submit',
        formaction: str = None,
        formmethod: Literal['POST', 'GET'] = None,
        formnovalidate: bool = None,
        formtarget: Literal['_blank', '_self', '_parent', '_top'] = None,
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        sanitize: bool = True,
    ):
        super().__init__(
            'submit', name, id, form, tabindex, classes, style,
            disabled, autofocus, None, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value
        self.formaction = formaction
        self.formmethod = formmethod
        self.formnovalidate = formnovalidate
        self.formtarget = formtarget
        self._sync_attrs()


class InputButton(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = 'Button',
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        sanitize: bool = True,
    ):
        super().__init__(
            'button', name, id, form, tabindex, classes, style,
            disabled, autofocus, None, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value


class InputReset(Input):
    def __init__(
        self,
        name: str = None,
        id: str = None,
        value: str = 'Reset',
        form=None,
        tabindex=None,
        classes=None,
        style=None,
        disabled=None,
        autofocus=None,
        onfocus: Callable = None,
        onblur: Callable = None,
        onchange: Callable = None,
        oninput: Callable = None,
        onclick: Callable = None,
        sanitize: bool = True,
    ):
        super().__init__(
            'reset', name, id, form, tabindex, classes, style,
            disabled, autofocus, None, onfocus, onblur, onchange, oninput, onclick,
        )
        self.sanitize = sanitize
        self.value = value
