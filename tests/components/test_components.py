import pytest

from pyweber.components.form import Form
from pyweber.components.general import Icon, Style, Script, Label, TextArea
from pyweber.components.input import (
    Input,
    InputButton,
    InputCheckbox,
    InputColor,
    InputDate,
    InputEmail,
    InputFile,
    InputHidden,
    InputNumber,
    InputPassword,
    InputRadio,
    InputReset,
    InputRange,
    InputSearch,
    InputSubmit,
    InputTel,
    InputText,
    InputTime,
    InputUrl,
)
from pyweber.utils.types import Icons


def _handler():
    return 'ok'


TEXT_INPUTS = [InputText, InputPassword, InputEmail, InputNumber, InputSearch, InputTel, InputUrl]
DATE_INPUTS = [InputColor, InputDate, InputTime]
SPECIAL_INPUTS = [InputHidden, InputCheckbox, InputRadio, InputRange, InputFile, InputSubmit, InputButton, InputReset]


@pytest.mark.parametrize('cls', TEXT_INPUTS)
def test_text_inputs(cls):
    inp = cls(
        name='n', id='i', value='v', placeholder='ph', disabled=True, required=True,
        autofocus=True, readonly=True, onclick=_handler,
    )
    assert 'input' in inp.to_html().lower()
    assert inp.onclick is _handler


@pytest.mark.parametrize('cls', DATE_INPUTS)
def test_date_inputs(cls):
    inp = cls(name='n', id='i', value='v', disabled=True, required=True, onclick=_handler)
    assert 'input' in inp.to_html().lower()


@pytest.mark.parametrize('cls', [InputHidden, InputRange, InputSubmit, InputButton, InputReset])
def test_special_inputs(cls):
    inp = cls(name='n', id='i', onclick=_handler)
    assert 'input' in inp.to_html().lower()
    assert inp.onclick is _handler


def test_input_checkbox_and_radio():
    cb = InputCheckbox(name='c', id='i', value='1', onclick=_handler)
    rd = InputRadio(name='r', id='i', value='a', onclick=_handler)
    assert cb.onclick is _handler
    assert rd.onclick is _handler


def test_input_file():
    inp = InputFile(name='f', id='i', accept='.txt', onclick=_handler)
    assert inp.type == 'file'
    assert inp.onclick is _handler


def test_input_attrs_immutable():
    inp = InputText(name='n')
    with pytest.raises(AttributeError):
        inp.attrs = {'bad': 'value'}


def test_input_boolean_attrs():
    inp = InputText(name='n', disabled=True, required=True, autofocus=True)
    assert 'disabled' in inp.attrs or inp.disabled is True


def test_form_element():
    form = Form(
        id='login',
        method='POST',
        action='/login',
        name='login-form',
        autocomplete='on',
        target='_blank',
        enctype='multipart/form-data',
        tabindex=1,
        onclick=_handler,
        onsubmit=_handler,
        onreset=_handler,
    )
    html = form.to_html()
    assert '<form' in html
    assert form.onsubmit is _handler


def test_form_attrs_immutable():
    form = Form()
    with pytest.raises(AttributeError):
        form.attrs = {'x': '1'}


def test_icon_with_enum_and_string():
    icon = Icon(list(Icons)[0])
    assert icon.tag == 'i'
    icon2 = Icon('custom-icon')
    assert 'custom-icon' in icon2.classes


def test_style_and_script():
    style = Style(href='/app.css')
    assert style.attrs['href'] == '/app.css'
    script = Script(src='/app.js', type='module', content='console.log(1)')
    assert 'console.log(1)' in script.to_html()


def test_script_attrs_immutable():
    script = Script()
    with pytest.raises(AttributeError):
        script.attrs = {'bad': '1'}


def test_label_and_textarea():
    label = Label(content='Name', to='name', form='f', tabindex=2)
    assert label.attrs.get('for') == 'name'
    area = TextArea(
        name='bio',
        id='bio',
        content='hello',
        rows=4,
        cols=40,
        maxlength=100,
        required=True,
        readonly=True,
        disabled=True,
        wrap='soft',
        placeholder='type here',
    )
    html = area.to_html()
    assert 'textarea' in html
