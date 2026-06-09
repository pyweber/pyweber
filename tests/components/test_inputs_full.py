"""Instancia cada input com os kwargs específicos da classe."""

from pyweber.components.input import (
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
    InputRange,
    InputReset,
    InputSearch,
    InputSubmit,
    InputTel,
    InputText,
    InputTime,
    InputUrl,
)


def test_input_text_full():
    el = InputText(
        name='t', id='t', value='v', placeholder='p', size=10, maxlength=5,
        minlength=1, pattern='.*', autocomplete='on', readonly=True, sanitize=True,
    )
    assert el.type == 'text'
    assert 'placeholder' in el.attrs


def test_input_password_full():
    el = InputPassword(name='p', showpassword=True, autocomplete='new-password')
    assert el.type == 'password'


def test_input_number_full():
    el = InputNumber(name='n', min=0, max=10, step=1)
    assert el.type == 'number'


def test_input_checkbox_and_radio():
    cb = InputCheckbox(name='c', checked=True, value='1')
    rd = InputRadio(name='r', checked=True, value='a')
    assert cb.type == 'checkbox'
    assert rd.type == 'radio'


def test_input_file_and_range():
    f = InputFile(name='f', accept='.png', multiple=True)
    r = InputRange(name='r', min=0, max=100, step=5, value=50)
    assert f.type == 'file'
    assert r.type == 'range'


def test_input_date_time_color():
    assert InputDate(name='d').type == 'date'
    assert InputTime(name='t').type == 'time'
    assert InputColor(name='c', value='#fff').type == 'color'


def test_input_search_tel_url():
    assert InputSearch(name='s').type == 'search'
    assert InputTel(name='t').type == 'tel'
    assert InputUrl(name='u').type == 'url'


def test_input_hidden_submit_button_reset():
    assert InputHidden(name='h', value='x').type == 'hidden'
    assert InputSubmit(name='s', formaction='/go').type == 'submit'
    assert InputButton(name='b').type == 'button'
    assert InputReset(name='r').type == 'reset'
