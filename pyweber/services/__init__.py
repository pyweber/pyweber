"""Internal collaborators used by ``Pyweber`` (composition over God Object bloat)."""

from pyweber.services.static_files import StaticFilesService
from pyweber.services.response_pipeline import ResponsePipeline
from pyweber.services.template_service import TemplateService
from pyweber.services.openapi_setup import OpenAPISetup

__all__ = [
    'StaticFilesService',
    'ResponsePipeline',
    'TemplateService',
    'OpenAPISetup',
]
