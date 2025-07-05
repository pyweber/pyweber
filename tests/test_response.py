import pytest
from unittest.mock import Mock, patch, PropertyMock
from datetime import datetime, timezone
from pyweber.models.response import Response
from pyweber.models.request import Request
from pyweber.utils.types import ContentTypes, HTTPStatusCode

class TestResponse:
    """Testes para a classe Response"""

    @pytest.fixture
    def mock_request(self):
        """Mock do objeto Request para os testes"""
        request = Mock(spec=Request)
        request.method = "GET"
        request.scheme = "HTTP/1.1"
        request.path = "/test"
        request.first_line = "GET /test HTTP/1.1"
        return request

    @pytest.fixture
    def sample_response(self, mock_request):
        """Response de exemplo para os testes"""
        return Response(
            request=mock_request,
            response_content=b"<html><body>Test</body></html>",
            code=200,
            cookies=["session=abc123", "user=john"],
            response_type=ContentTypes.html,  # Corrigido para minúsculo
            route="/test"
        )

    def test_init_creates_response_with_correct_attributes(self, mock_request):
        """Testa se a inicialização cria o Response com atributos corretos"""
        content = b"Test content"
        code = 200
        cookies = ["test=value"]
        response_type = ContentTypes.json  # Corrigido para minúsculo
        route = "/api/test"

        response = Response(
            request=mock_request,
            response_content=content,
            code=code,
            cookies=cookies,
            response_type=response_type,
            route=route
        )

        assert response.request == mock_request
        assert response.response_content == content
        assert response.code == code
        assert response.cookies == cookies
        assert response.request_path == "/test"
        assert response.response_path == route

    def test_headers_property_returns_correct_headers(self, sample_response):
        """Testa se a propriedade headers retorna os cabeçalhos corretos"""
        headers = sample_response.headers

        assert headers["Content-Type"] == "text/html; charset=UTF-8"
        assert headers["Content-Length"] == 30  # len(b"<html><body>Test</body></html>")
        assert headers["Connection"] == "Close"
        assert headers["Method"] == "GET"
        assert headers["Http-Version"] == "HTTP/1.1"
        assert headers["Status"] == 200
        assert headers["Server"] == "Pyweber/1.0"
        assert "Date" in headers
        assert headers["Set-Cookie"] == ["session=abc123", "user=john"]
        assert headers["Request-Path"] == "/test"
        assert headers["Response-Path"] == "/test"

    def test_http_version_property(self, sample_response):
        """Testa a propriedade http_version"""
        assert sample_response.http_version == "HTTP/1.1"

    def test_response_date_property(self, sample_response):
        """Testa a propriedade response_date"""
        date = sample_response.response_date
        assert date is not None
        assert isinstance(date, str)
        # Verifica formato GMT
        assert "GMT" in date

    def test_response_type_property(self, sample_response):
        """Testa a propriedade response_type"""
        assert sample_response.response_type == "text/html; charset=UTF-8"

    def test_response_content_property(self, sample_response):
        """Testa a propriedade response_content"""
        assert sample_response.response_content == b"<html><body>Test</body></html>"

    def test_cookies_property(self, sample_response):
        """Testa a propriedade cookies"""
        assert sample_response.cookies == ["session=abc123", "user=john"]

    def test_code_property(self, sample_response):
        """Testa a propriedade code"""
        assert sample_response.code == 200

    def test_request_path_property(self, sample_response):
        """Testa a propriedade request_path"""
        assert sample_response.request_path == "/test"

    def test_response_path_property(self, sample_response):
        """Testa a propriedade response_path"""
        assert sample_response.response_path == "/test"

    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_status_code_property_2xx(self, mock_search, sample_response):
        """Testa status_code para códigos 2xx"""
        mock_search.return_value = "200 OK"
        assert sample_response.status_code == "200 OK"

    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_status_code_property_3xx_redirect(self, mock_search, mock_request):
        """Testa status_code para códigos 3xx (redirecionamento)"""
        mock_search.return_value = "301 Moved Permanently"

        response = Response(
            request=mock_request,
            response_content=b"",
            code=301,
            cookies=[],
            response_type=ContentTypes.html,  # Corrigido para minúsculo
            route="/new-location"
        )

        expected = "301 Moved Permanently\r\nLocation: /new-location"
        assert response.status_code == expected

    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_status_code_property_405_method_not_allowed(self, mock_search, mock_request):
        """Testa status_code para 405 Method Not Allowed"""
        mock_search.return_value = "405 Method Not Allowed"

        response = Response(
            request=mock_request,
            response_content=b"",
            code=405,
            cookies=[],
            response_type=ContentTypes.html,  # Corrigido para minúsculo
            route="/api"
        )

        expected = "405 Method Not Allowed\r\nAllow: GET, POST, PUT, DELETE"
        assert response.status_code == expected

    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_status_code_property_503_service_unavailable(self, mock_search, mock_request):
        """Testa status_code para 503 Service Unavailable"""
        mock_search.return_value = "503 Service Unavailable"

        response = Response(
            request=mock_request,
            response_content=b"",
            code=503,
            cookies=[],
            response_type=ContentTypes.html,  # Corrigido para minúsculo
            route="/api"
        )

        expected = "503 Service Unavailable\r\nRetry-After: 60"
        assert response.status_code == expected

    def test_getitem_no_key(self, sample_response):
        """Testa __getitem__ sem chave"""
        result = sample_response[None]
        expected = {
            'headers': sample_response.headers,
            'body': sample_response.response_content
        }
        assert result == expected

    def test_getitem_headers_key(self, sample_response):
        """Testa __getitem__ com chave 'headers'"""
        result = sample_response['headers']
        assert result == sample_response.headers

    def test_getitem_body_key(self, sample_response):
        """Testa __getitem__ com chave 'body'"""
        result = sample_response['body']
        assert result == sample_response.response_content

    def test_getitem_invalid_key(self, sample_response):
        """Testa __getitem__ com chave inválida"""
        result = sample_response['invalid']
        assert result == {}

    def test_set_header(self, sample_response):
        """Testa o método set_header"""
        sample_response.set_header("X-Custom-Header", "custom-value")
        assert sample_response.headers["X-Custom-Header"] == "custom-value"

    def test_update_header_existing(self, sample_response):
        """Testa update_header para cabeçalho existente"""
        original_length = sample_response.headers["Content-Length"]
        sample_response.update_header("Content-Length", 100)
        assert sample_response.headers["Content-Length"] == 100
        assert sample_response.headers["Content-Length"] != original_length

    def test_update_header_non_existing(self, sample_response):
        """Testa update_header para cabeçalho inexistente"""
        original_headers_count = len(sample_response.headers)
        sample_response.update_header("Non-Existing", "value")
        # Não deve adicionar novo cabeçalho
        assert len(sample_response.headers) == original_headers_count
        assert "Non-Existing" not in sample_response.headers

    def test_new_content_valid_bytes(self, sample_response):
        """Testa new_content com bytes válidos"""
        new_content = b"New content here"
        sample_response.new_content(new_content)

        assert sample_response.response_content == new_content
        assert sample_response.headers["Content-Length"] == len(new_content)

    def test_new_content_invalid_type(self, sample_response):
        """Testa new_content com tipo inválido"""
        original_content = sample_response.response_content
        original_length = sample_response.headers["Content-Length"]

        # Tentativa com string (não bytes)
        sample_response.new_content("Not bytes")

        # Conteúdo não deve mudar
        assert sample_response.response_content == original_content
        assert sample_response.headers["Content-Length"] == original_length

    @patch('pyweber.utils.utils.PrintLine')
    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_build_response_structure(self, mock_search, mock_print, sample_response):
        """Testa a estrutura do build_response"""
        mock_search.return_value = "200 OK"

        result = sample_response.build_response

        # Deve ser bytes
        assert isinstance(result, bytes)

        # Deve conter a primeira linha HTTP
        result_str = result.decode()
        assert "HTTP/1.1 200 OK" in result_str

        # Deve conter cabeçalhos
        assert "Content-Type: text/html; charset=UTF-8" in result_str
        assert "Content-Length: 30" in result_str

        # Deve conter o corpo
        assert result.endswith(b"<html><body>Test</body></html>")

    @patch('pyweber.utils.utils.PrintLine')
    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_build_response_with_cookies(self, mock_search, mock_print, sample_response):
        """Testa build_response com cookies"""
        mock_search.return_value = "200 OK"

        result = sample_response.build_response
        result_str = result.decode()

        # Deve conter ambos os cookies
        assert "Set-Cookie: session=abc123" in result_str
        assert "Set-Cookie: user=john" in result_str

    @patch('pyweber.utils.utils.PrintLine')
    @patch('pyweber.utils.types.HTTPStatusCode.search_by_code')
    def test_build_response_color_coding(self, mock_search, mock_print, mock_request):
        """Testa a codificação de cores no build_response"""
        # Teste para diferentes códigos de status
        test_cases = [
            (200, "200 OK"),
            (301, "301 Moved Permanently"),
            (404, "404 Not Found"),
            (500, "500 Internal Server Error"),
            (100, "100 Continue"),
        ]

        for code, status_text in test_cases:
            mock_search.return_value = status_text

            response = Response(
                request=mock_request,
                response_content=b"test",
                code=code,
                cookies=[],
                response_type=ContentTypes.html,  # Corrigido para minúsculo
                route="/test"
            )

            result = response.build_response
            assert isinstance(result, bytes)

            # Reset mock para próxima iteração
            mock_print.reset_mock()

    def test_response_with_different_content_types(self, mock_request):
        """Testa Response com diferentes tipos de conteúdo"""
        content_types = [
            (ContentTypes.json, "application/json; charset=UTF-8"),
            (ContentTypes.html, "text/html; charset=UTF-8"),
            (ContentTypes.css, "text/css; charset=UTF-8"),
            (ContentTypes.js, "application/javascript; charset=UTF-8"),  # Corrigido para 'js'
        ]

        for content_type, expected_header in content_types:
            response = Response(
                request=mock_request,
                response_content=b"test content",
                code=200,
                cookies=[],
                response_type=content_type,
                route="/test"
            )

            assert response.headers["Content-Type"] == expected_header

    def test_response_with_empty_content(self, mock_request):
        """Testa Response com conteúdo vazio"""
        response = Response(
            request=mock_request,
            response_content=b"",
            code=204,
            cookies=[],
            response_type=ContentTypes.html,  # Corrigido para minúsculo
            route="/empty"
        )

        assert response.response_content == b""
        assert response.headers["Content-Length"] == 0

    def test_response_with_large_content(self, mock_request):
        """Testa Response com conteúdo grande"""
        large_content = b"x" * 10000
        response = Response(
            request=mock_request,
            response_content=large_content,
            code=200,
            cookies=[],
            response_type=ContentTypes.html,  # Corrigido para minúsculo
            route="/large"
        )

        assert response.response_content == large_content
        assert response.headers["Content-Length"] == 10000


# Testes de integração
class TestResponseIntegration:
    """Testes de integração para a classe Response"""

    def test_complete_response_cycle(self):
        """Testa um ciclo completo de criação e uso do Response"""
        # Mock do request
        request = Mock(spec=Request)
        request.method = "POST"
        request.scheme = "HTTP/1.1"
        request.path = "/api/users"
        request.first_line = "POST /api/users HTTP/1.1"

        # Criação do response
        response = Response(
            request=request,
            response_content=b'{"id": 1, "name": "John"}',
            code=201,
            cookies=["auth=token123"],
            response_type=ContentTypes.json,  # Corrigido para minúsculo
            route="/api/users"
        )

        # Modificações
        response.set_header("X-API-Version", "1.0")
        response.update_header("Server", "Pyweber/2.0")
        response.new_content(b'{"id": 1, "name": "John", "created": true}')

        # Verificações
        assert response.code == 201
        assert response.headers["X-API-Version"] == "1.0"
        assert response.headers["Server"] == "Pyweber/2.0"
        assert b"created" in response.response_content
        assert response.headers["Content-Length"] == len(response.response_content)

        # Build final
        with patch('pyweber.utils.utils.PrintLine'), \
             patch('pyweber.utils.types.HTTPStatusCode.search_by_code', return_value="201 Created"):
            final_response = response.build_response
            assert isinstance(final_response, bytes)
            assert b"HTTP/1.1" in final_response
            assert b"application/json" in final_response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
