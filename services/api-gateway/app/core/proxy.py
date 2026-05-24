"""
proxy.py — Request routing and forwarding for the API Gateway.

The gateway is not a business service. It has one job: inspect the URL path,
determine which downstream service owns that path, and forward the request
with full fidelity — method, headers, body, and query parameters preserved.

Service routing table (from the architecture doc):
  /auth/*          → User Service          :8001
  /users/*         → User Service          :8001
  /traffic-data/*  → Traffic Intelligence  :8002
  /predict/*       → Traffic Intelligence  :8002
  /model/*         → Traffic Intelligence  :8002
  /incidents/*     → Incident Report       :8004
  /notifications/* → Notification Service  :8003
  /chat/* Rag Service : 8005
"""

import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import Response

from app.config import settings


def _build_routing_table() -> list[tuple[str, str]]:
    """
    Build the path-prefix → service URL routing table.

    Returns a list of (prefix, url) tuples ordered longest-prefix first so
    that more specific prefixes match before shorter ones. This prevents
    /predict/route from accidentally matching a hypothetical /pre prefix.
    """
    raw = {
        "/auth":           settings.USER_SERVICE_URL,
        "/users":          settings.USER_SERVICE_URL,
        "/traffic-data":   settings.TRAFFIC_SERVICE_URL,
        "/predict":        settings.TRAFFIC_SERVICE_URL,
        "/model":          settings.TRAFFIC_SERVICE_URL,
        "/incidents":      settings.INCIDENT_SERVICE_URL,
        "/notifications":  settings.NOTIFICATION_SERVICE_URL,
        "/chat":           settings.RAG_SERVICE_URL,
    }
    # Sort by prefix length descending — longest match wins.
    return sorted(raw.items(), key=lambda item: len(item[0]), reverse=True)


# Built once at import time. Settings are already loaded from .env by then.
ROUTING_TABLE: list[tuple[str, str]] = _build_routing_table()


def resolve_service_url(path: str) -> str | None:
    """
    Walk the routing table and return the base URL of the service that owns
    the given path. Returns None if no prefix matches.

    Args:
        path: The full URL path of the incoming request (e.g. /incidents/near).

    Returns:
        The service base URL (e.g. http://incident-report-service:8004),
        or None if the path is unrecognised.
    """
    for prefix, service_url in ROUTING_TABLE:
        if path.startswith(prefix):
            return service_url
    return None


async def route_request(request: Request, client: httpx.AsyncClient) -> Response:
    """
    Forward the incoming request to the correct downstream service and
    return its response to the client unchanged.

    Preserves:
      - HTTP method (GET, POST, PUT, DELETE, PATCH)
      - URL path and query string
      - Request headers (minus the Host header — Docker handles DNS)
      - Request body (JSON, form data, binary — whatever was sent)
      - Response status code, headers, and body

    Args:
        request: The raw FastAPI Request object from the gateway endpoint.
        client:  The shared httpx.AsyncClient stored on app.state at startup.

    Returns:
        A FastAPI Response with the downstream service's status, headers,
        and body forwarded verbatim.

    Raises:
        HTTPException 404 if no service is mapped to the path.
        HTTPException 502 if the downstream service is unreachable.
        HTTPException 504 if the downstream service times out.
    """
    path = request.url.path

    # ----------------------------------------------------------------
    # Resolve the target service from the routing table.
    # ----------------------------------------------------------------
    target_base = resolve_service_url(path)

    if target_base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No service is registered for path: {path}",
        )

    # ----------------------------------------------------------------
    # Build the full forwarding URL, including query string.
    # ----------------------------------------------------------------
    target_url = f"{target_base}{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # ----------------------------------------------------------------
    # Copy headers. The Host header must be dropped — it contains the
    # gateway's own hostname. Each downstream service has its own host
    # inside Docker and httpx will set the correct Host automatically.
    # ----------------------------------------------------------------
   

    forward_headers = {
    key: value
    for key, value in request.headers.items()
    if key.lower() not in {"host", "content-length"}
}
    # ----------------------------------------------------------------
    # Read the request body once. httpx sends it as raw bytes so all
    # content types (JSON, form data, multipart, binary) are preserved.
    # ----------------------------------------------------------------
    
    import json

    body = await request.body()

    if path.startswith("/incidents") and request.method == "POST":
        user_id = getattr(request.state, "user_id", None)
        if user_id and body:
            try:
                body_data = json.loads(body)
                body_data["reported_by"] = user_id
                body = json.dumps(body_data).encode()
            except json.JSONDecodeError:
                pass

    # ----------------------------------------------------------------
    # Forward the request.
    # ----------------------------------------------------------------
    try:
        downstream_response = await client.request(
            method=request.method,
            url=target_url,
            headers=forward_headers,
            content=body,
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not connect to downstream service at {target_base}. "
                   "Ensure the service container is running.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Downstream service at {target_base} did not respond in time.",
        )

    # ----------------------------------------------------------------
    # Return the downstream response to the original caller.
    # Strip transfer-encoding — httpx buffers the full response body,
    # so chunked encoding headers from the downstream are irrelevant
    # and would confuse some clients if forwarded as-is.
    # ----------------------------------------------------------------
    excluded_response_headers = {"transfer-encoding", "content-encoding"}
    response_headers = {
        key: value
        for key, value in downstream_response.headers.items()
        if key.lower() not in excluded_response_headers
    }

    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=response_headers,
        media_type=downstream_response.headers.get("content-type"),
    )




async def forward_websocket(websocket_path: str, token: str, client_websocket):
    """
    Forward a WebSocket connection from the client to the notification service.
    Bridges two WebSocket connections — client <-> gateway <-> notification service.
    """
    import websockets as ws

    target_base = settings.NOTIFICATION_SERVICE_URL.replace("http://", "ws://")
    target_url = f"{target_base}{websocket_path}"

    try:
        async with ws.connect(target_url) as downstream_ws:
            async def client_to_downstream():
                try:
                    while True:
                        data = await client_websocket.receive_text()
                        await downstream_ws.send(data)
                except Exception:
                    pass

            async def downstream_to_client():
                try:
                    async for message in downstream_ws:
                        await client_websocket.send_text(message)
                except Exception:
                    pass

            import asyncio
            await asyncio.gather(
                client_to_downstream(),
                downstream_to_client(),
            )
    except Exception as e:
        logger.error("WebSocket forwarding error: %s", e)