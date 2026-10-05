"""OpenAPI /docs route registration."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import TYPE_CHECKING

from pyweber.models.openapi import OpenAPIBuilder, OpenAPIConfig
from pyweber.models.routes import Route
from pyweber.utils.security import CSRF_COOKIE_NAME, CSRF_HEADER, is_production
from pyweber.utils.types import ContentTypes, StaticFilePath

if TYPE_CHECKING:
    from pyweber.pyweber.pyweber import Pyweber


class OpenAPISetup:
    """Register documentation routes from ``OpenAPIConfig``."""

    def __init__(self, app: Pyweber):
        self.app = app

    def setup_routes(self) -> None:
        config = self.app.openapi or OpenAPIConfig()
        routes: list[Route] = []

        expose = bool(getattr(config, 'expose_in_production', False))
        if is_production() and not expose:
            return

        docs_security = getattr(config, 'docs_security', None)
        if docs_security is None:
            docs_security = []

        if config.docs_url:
            routes.append(
                Route(
                    route=config.docs_url,
                    template=self.render_docs_page,
                    content_type=ContentTypes.html,
                    process_response=False,
                    title='Pyweber Documentation',
                    security=docs_security,
                    include_in_schema=False,
                )
            )

        if config.openapi_url:
            routes.append(
                Route(
                    route=config.openapi_url,
                    template=self.app.get_openapi_schema,
                    content_type=ContentTypes.json,
                    process_response=False,
                    security=docs_security,
                    include_in_schema=False,
                    title='OpenAPI Schema',
                )
            )
            routes.append(
                Route(
                    route='/_pyweber/{uuid}/openapi.json',
                    template=self.app.get_openapi_schema,
                    content_type=ContentTypes.json,
                    process_response=False,
                    security=docs_security,
                    include_in_schema=False,
                    title='OpenAPI Schema',
                )
            )

        if routes:
            self.app.add_group_routes(routes)

    def build_schema(self, **kwargs):
        return OpenAPIBuilder(self.app).build()

    def swagger_ui_options(self) -> dict:
        config = self.app.openapi or OpenAPIConfig()
        options = {
            'url': config.openapi_url or '/openapi.json',
            'deepLinking': True,
            'persistAuthorization': True,
            'displayRequestDuration': True,
            'filter': True,
            'docExpansion': 'list',
            'tryItOutEnabled': False,
            'operationsSorter': 'alpha',
            'tagsSorter': 'alpha',
        }
        options.update(config.swagger_ui_parameters or {})
        return options

    def render_docs_page(self, **kwargs) -> str:
        config = self.app.openapi or OpenAPIConfig()
        template = Path(str(StaticFilePath.pyweber_docs.value)).read_text(encoding='utf-8')
        # "</" inside inline JSON would close the <script> tag early.
        options = json.dumps(self.swagger_ui_options()).replace('</', '<\\/')
        return (
            template
            .replace('{{TITLE}}', html.escape(config.title or 'API docs'))
            .replace('{{CONFIG}}', options)
            .replace('{{CSRF_COOKIE}}', CSRF_COOKIE_NAME)
            .replace('{{CSRF_HEADER}}', CSRF_HEADER)
        )
