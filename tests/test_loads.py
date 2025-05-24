import pytest
from pyweber.utils.loads import StaticTemplates

def test_loads():
    assert isinstance(StaticTemplates.BASE_CSS(), str)
    assert isinstance(StaticTemplates.BASE_HTML(), str)
    assert isinstance(StaticTemplates.BASE_MAIN(), str)
    assert isinstance(StaticTemplates.CONFIG_DEFAULT(), dict)
    assert isinstance(StaticTemplates.FAVICON(), bytes)
    assert isinstance(StaticTemplates.JS_STATIC(), str)
    assert isinstance(StaticTemplates.PAGE_NOT_FOUND(), str)
    assert isinstance(StaticTemplates.PAGE_SERVER_ERROR(), str)
    assert isinstance(StaticTemplates.PAGE_UNAUTHORIZED(), str)
    assert isinstance(StaticTemplates.UPDATE_FILE(), str)