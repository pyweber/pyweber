"""Regressions for __inject_default_elements (favicon, css, scripts)."""

from pyweber.core.template import Template


def _icon_links(template: Template):
    head = template.root.querySelector('head')
    if not head:
        return []
    return [
        link for link in head.querySelectorAll('link')
        if 'icon' in (link.get_attr('rel') or '').lower()
        or 'favicon' in (link.get_attr('href') or '').lower()
        or (link.get_attr('href') or '').endswith('.ico')
    ]


def test_parse_html_does_not_duplicate_favicon_with_rel_icon():
    t = Template(template='<html><head></head><body></body></html>')
    html = '<html><head><link rel="icon" href="/favicon.ico"></head><body></body></html>'
    t.root = t.parse_html(html=html)
    assert len(_icon_links(t)) == 1


def test_parse_html_does_not_duplicate_shortcut_icon():
    t = Template(template='<html><head></head><body></body></html>')
    html = '<html><head><link rel="shortcut icon" href="/f.ico"></head><body></body></html>'
    t.root = t.parse_html(html=html)
    assert len(_icon_links(t)) == 1


def test_resync_parse_does_not_add_second_favicon():
    t = Template(template='<html><head></head><body></body></html>')
    html = '<html><head><link rel="icon" href="/favicon.ico"></head><body></body></html>'
    t.root = t.parse_html(html=html)
    assert len(_icon_links(t)) == 1
    t.root = t.parse_html(html=t.build_html())
    assert len(_icon_links(t)) == 1


def test_parse_html_does_not_duplicate_apple_touch_icon():
    t = Template(template='<html><head></head><body></body></html>')
    html = '<html><head><link rel="apple-touch-icon" href="/apple.png"></head><body></body></html>'
    t.root = t.parse_html(html=html)
    assert len(_icon_links(t)) == 1


def test_existing_stylesheet_skips_default_pyweber_css():
    t = Template(template='<html><head></head><body></body></html>')
    html = '<html><head><link rel="stylesheet" href="/bootstrap-icons.css"></head><body></body></html>'
    t.root = t.parse_html(html=html)
    head = t.root.querySelector('head')
    pyweber_css = [
        link for link in head.querySelectorAll('link')
        if (link.get_attr('href') or '').startswith('/_pyweber/static/')
        and (link.get_attr('rel') or '').lower() == 'stylesheet'
    ]
    assert pyweber_css == []
