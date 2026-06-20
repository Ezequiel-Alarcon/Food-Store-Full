"""
tests/integration/test_rate_limit.py
======================================

Pruebas de integración del RateLimitMiddleware.

Verificamos:
  - El rate limit devuelve 429 cuando se excede.
  - Los headers X-RateLimit-* están presentes.
  - El rate limit en endpoints de auth es más estricto.
"""

import pytest
from fastapi.testclient import TestClient

class TestRateLimitDefault:

    def test_response_includes_ratelimit_headers(self, client: TestClient):
        """Toda respuesta de un endpoint rate-limiteado incluye X-RateLimit-*."""
        response = client.get("/api/v1/productos/")
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers

    def test_429_when_burst_exhausted(self, client: TestClient):
        """Agotar la ráfaga inicial devuelve 429."""
        # Con RATE_LIMIT_DEFAULT_BURST=10, el 11vo request dispara el 429.
        statuses = [client.get("/api/v1/productos/").status_code for _ in range(15)]
        assert 429 in statuses

    def test_429_includes_retry_after(self, client: TestClient):
        """El 429 incluye el header Retry-After con un entero positivo."""
        for _ in range(15):
            r = client.get("/api/v1/productos/")
            if r.status_code == 429:
                assert "retry-after" in r.headers
                assert int(r.headers["retry-after"]) > 0
                return
        pytest.fail("No se alcanzó el 429 luego de 15 requests")

class TestRateLimitAuth:

    def test_auth_endpoint_has_stricter_limit(self, client: TestClient):
        """El limiter de auth se agota antes que el general."""
        # Con RATE_LIMIT_AUTH_BURST=5, el 6to request de login dispara el 429.
        statuses = []
        for _ in range(10):
            r = client.post(
                "/api/v1/auth/login",
                data={"username": "nobody@x.com", "password": "wrong"},
            )
            statuses.append(r.status_code)
        assert 429 in statuses
