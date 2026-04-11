from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import httpx
import os

app = FastAPI(
    title="UrbanFlow API Gateway",
    description="Single entry point for all UrbanFlow microservices",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
MOBILITY_SERVICE_URL = os.getenv("MOBILITY_SERVICE_URL", "http://mobility-intelligence-service:8002")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8003")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}


@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_user_service(path: str, request: Request):
    return await _proxy(request, f"{USER_SERVICE_URL}/users/{path}")


@app.api_route("/mobility/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_mobility_service(path: str, request: Request):
    return await _proxy(request, f"{MOBILITY_SERVICE_URL}/mobility/{path}")


@app.api_route("/notifications/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_notification_service(path: str, request: Request):
    return await _proxy(request, f"{NOTIFICATION_SERVICE_URL}/notifications/{path}")


async def _proxy(request: Request, url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers={k: v for k, v in request.headers.items() if k != "host"},
                content=await request.body(),
                timeout=30.0
            )
            from fastapi.responses import Response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Service unavailable")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Service timeout")
