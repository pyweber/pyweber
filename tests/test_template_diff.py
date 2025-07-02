import pytest
from pyweber.models.template_diff import TemplateDiff
from pyweber.core.element import Element

class FakeElement(Element):
    def __init__(self, uuid, id=None, content=None, value=None, tag=None, attrs=None, style=None, events=None, classes=None, parent=None, childs=None):
        super().__init__(tag=tag or 'div')
        self.uuid = uuid
        self.id = id or ''
        self.content = content or ''
        self.value = value or ''
        self.tag = tag or ''
        self.attrs = attrs or {}
        self.style = style or {}
        self.events = events or type("Events", (), {})()  # Empty class
        self.classes = classes or []
        self.parent = parent
        self.childs = childs or []

    def to_html(self):
        return f"<div id='{self.id}'>{self.content}</div>"

# ---------------------------
# Testes individuais
# ---------------------------

def test_element_added():
    new_element = FakeElement(uuid="1")
    old_element = FakeElement(uuid="2")  # Different UUID = added/removed
    diff = TemplateDiff()

    diff.track_differences(new_element, old_element)

    assert any(d['status'] == 'Added' for d in diff.differences.values())
    assert any(d['status'] == 'Removed' for d in diff.differences.values())

def test_element_changed_content():
    base_uuid = "123"
    old_element = FakeElement(uuid=base_uuid, content="Old")
    new_element = FakeElement(uuid=base_uuid, content="New")
    diff = TemplateDiff()

    diff.track_differences(new_element, old_element)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_same_no_diff():
    elem = FakeElement(uuid="xyz", content="Same")
    diff = TemplateDiff()

    diff.track_differences(elem, elem)
    assert len(diff.differences) == 0

def test_element_with_child_added():
    parent_uuid = "parent"
    child_old = FakeElement(uuid="child1")
    child_new = FakeElement(uuid="child2")

    old_element = FakeElement(uuid=parent_uuid, childs=[child_old])
    new_element = FakeElement(uuid=parent_uuid, childs=[child_new])

    child_new.parent = new_element
    child_old.parent = old_element

    diff = TemplateDiff()

    diff.track_differences(new_element, old_element)

    assert any(d['status'] == 'Added' for d in diff.differences.values())
    assert any(d['status'] == 'Removed' for d in diff.differences.values())

def test_element_differs_by_id():
    elem1 = FakeElement(uuid="1", id="a")
    elem2 = FakeElement(uuid="1", id="b")
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_differs_by_content():
    elem1 = FakeElement(uuid="1", content="new")
    elem2 = FakeElement(uuid="1", content="old")
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_differs_by_value():
    elem1 = FakeElement(uuid="1", value="v1")
    elem2 = FakeElement(uuid="1", value="v2")
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_differs_by_tag():
    elem1 = FakeElement(uuid="1", tag="div")
    elem2 = FakeElement(uuid="1", tag="span")
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_differs_by_attrs():
    elem1 = FakeElement(uuid="1", attrs={"href": "/home"})
    elem2 = FakeElement(uuid="1", attrs={"href": "/about"})
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_differs_by_style():
    elem1 = FakeElement(uuid="1", style={"color": "red"})
    elem2 = FakeElement(uuid="1", style={"color": "blue"})
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

class Events:
    def __init__(self, onclick=None):
        self.onclick = onclick

def test_element_differs_by_events():
    e1 = FakeElement(uuid="1")
    e2 = FakeElement(uuid="1")
    e1.events = Events(onclick="handler1")
    e2.events = Events(onclick="handler2")
    diff = TemplateDiff()

    diff.track_differences(e1, e2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_element_differs_by_classes():
    elem1 = FakeElement(uuid="1", classes=["btn", "primary"])
    elem2 = FakeElement(uuid="1", classes=["btn"])
    diff = TemplateDiff()

    diff.track_differences(elem1, elem2)
    assert any(d['status'] == 'Changed' for d in diff.differences.values())

def test_child_with_parent_not_in_checked_elements():
    parent_uuid = "parent-1"
    child_uuid = "child-1"

    parent_old = FakeElement(uuid=parent_uuid)
    parent_new = FakeElement(uuid=parent_uuid)

    child_old = FakeElement(uuid=child_uuid, parent=parent_old)
    child_new = FakeElement(uuid=child_uuid, parent=parent_new)

    parent_old.childs = [child_old]
    parent_new.childs = [child_new]

    diff = TemplateDiff()

    diff.track_differences(parent_new, parent_old)

    # Assert that the child's UUID was tracked (indicating the line ran)
    assert child_uuid not in [e.uuid for e in diff._TemplateDiff__checked_elements]
