"""
test_middleware.py — Tests for app/core/middleware.py

Verifies that CORS middleware is correctly registered on the app.
Covers the register_middleware() function and its allowed origins.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestCORSMiddleware:

    def test_cors_headers_present_on_options_request(self):
        """
        An OPTIONS preflight request from an allowed origin should receive
        CORS headers back. This confirms middleware is registered correctly.
        """
        from app.core.middleware import register_middleware

        app = FastAPI()
        register_middleware(app)

        @app.get("/test")
        def test_route():
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        response = client.options(
            "/test",
            headers={
                "Origin": "http://194.163.153.164:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" in response.headers

    def test_allowed_origin_receives_cors_header(self):
        """
        A GET request from an allowed origin should receive the
        Access-Control-Allow-Origin header in the response.
        """
        from app.core.middleware import register_middleware

        app = FastAPI()
        register_middleware(app)

        @app.get("/test")
        def test_route():
            return {"ok": True}

        client = TestClient(app)
        response = client.get(
            "/test",
            headers={"Origin": "http://194.163.153.164:5173"},
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_register_middleware_does_not_raise(self):
        """
        register_middleware() should run without raising any exceptions
        when given a valid FastAPI app instance.
        """
        from app.core.middleware import register_middleware

        app = FastAPI()
        try:
            register_middleware(app)
        except Exception as e:
            pytest.fail(f"register_middleware() raised an exception: {e}")

    def test_credentials_allowed(self):
        """
        allow_credentials=True means the response must include
        Access-Control-Allow-Credentials: true for credentialed requests.
        """
        from app.core.middleware import register_middleware

        app = FastAPI()
        register_middleware(app)

        @app.get("/test")
        def test_route():
            return {"ok": True}

        client = TestClient(app)
        response = client.get(
            "/test",
            headers={"Origin": "http://194.163.153.164:5173"},
        )
        assert response.headers.get("access-control-allow-credentials") == "true"