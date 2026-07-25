"""Middleware qui genere/propage un identifiant de requete unique.

L'identifiant est :
- injecte dans le header de reponse 'X-Request-ID'
- accessible via request.state.request_id pour etre ajoute aux logs applicatifs
"""
import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("stageflow.request")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        logger.info(
            "request_start",
            extra={"request_id": request_id, "path": request.url.path, "method": request.method},
        )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_end",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "status_code": response.status_code,
            },
        )
        return response
