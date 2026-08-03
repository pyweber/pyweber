"""Template / content serialization helpers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Union

from pyweber.core.element import Element
from pyweber.core.template import Template
from pyweber.models.response import Response
from pyweber.utils.types import ContentTypes

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import ContentResult, TemplateResult


class TemplateService:
    """Serialize templates/elements/JSON into ``ContentResult``."""

    def should_register_handoff(self, template_result: TemplateResult) -> bool:
        if not (
            template_result.process_response
            and template_result.content_type == ContentTypes.html
            and 200 <= template_result.status_code < 300
        ):
            return False

        template = template_result.template
        if isinstance(template, (dict, list, set, Response)):
            return False
        if isinstance(template, Template) and not template.include_uuid:
            return False
        if isinstance(template, Element) and not getattr(template, 'include_uuid', True):
            return False
        return True

    def ensure_template_object(
        self,
        template: Union[Template, Element, str],
        title: str = None,
    ) -> Template:
        if isinstance(template, Response):
            raise TypeError('Response cannot be converted to Template for handoff')
        if isinstance(template, Template):
            return template
        if isinstance(template, Element):
            return Template(template=template.to_html(), title=title)
        return Template(template=str(template), title=title)

    def template_to_bytes(
        self,
        template: Union[Template, Element, dict, list, set, str, bytes],
        content_type: ContentTypes = ContentTypes.html,
        title: str = None,
        process_response: bool = False,
    ):
        from pyweber.pyweber.pyweber import ContentResult

        if isinstance(template, Template):
            return self._process_template_object(
                template=template, title=title, content_type=content_type
            )
        if isinstance(template, Element):
            return self._process_element_object(
                element=template,
                title=title,
                content_type=content_type,
                process_template=process_response,
            )
        if isinstance(template, (dict, set, list)):
            return self._process_json_object(template=template)
        if isinstance(template, bytes):
            return self._process_byte_object(data=template, content_type=content_type)
        if isinstance(template, Response):
            return template
        return self._process_string_object(
            data=template,
            title=title,
            content_type=content_type,
            process_response=process_response,
        )

    def _process_byte_object(self, data: bytes, content_type: ContentTypes):
        from pyweber.pyweber.pyweber import ContentResult
        return ContentResult(content=data, content_type=content_type)

    def _process_json_object(self, template: Union[dict, list, set]):
        from pyweber.pyweber.pyweber import ContentResult
        return ContentResult(content=json.dumps(template).encode(), content_type=ContentTypes.json)

    def _process_template_object(self, template: Template, title: str, content_type: ContentTypes):
        from pyweber.pyweber.pyweber import ContentResult
        template.title = title if title else template.title
        return ContentResult(content=template.build_html().encode(), content_type=content_type)

    def _process_element_object(
        self,
        element: Element,
        title: str,
        content_type: ContentTypes,
        process_template: bool,
    ):
        from pyweber.pyweber.pyweber import ContentResult
        if process_template:
            return ContentResult(
                content=Template(template=element.to_html(), title=title).build_html().encode(),
                content_type=content_type,
            )
        return ContentResult(content=element.to_html().encode(), content_type=content_type)

    def _process_string_object(
        self,
        data: str,
        title: str,
        content_type: ContentTypes,
        process_response: bool,
    ):
        from pyweber.pyweber.pyweber import ContentResult
        if not isinstance(data, str):
            data = str(data)
        if process_response and content_type == ContentTypes.html:
            return ContentResult(
                content=Template(template=data, title=title).build_html().encode(),
                content_type=content_type,
            )
        return ContentResult(content=data.encode(), content_type=content_type)
