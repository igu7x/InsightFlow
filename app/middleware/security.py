from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings

# Origens externas usadas pelas páginas. Ficam declaradas uma única vez para
# que a política continue restritiva: nada de curingas e nada de
# 'unsafe-inline' em script-src, o que exige que todo JavaScript da aplicação
# esteja em arquivos servidos por /static.
CDN = "https://cdn.jsdelivr.net"
FONTES_CSS = "https://fonts.googleapis.com"
FONTES_ARQUIVOS = "https://fonts.gstatic.com"

CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        f"script-src 'self' {CDN}",
        f"style-src 'self' 'unsafe-inline' {CDN} {FONTES_CSS}",
        f"font-src 'self' {CDN} {FONTES_ARQUIVOS}",
        "img-src 'self' data:",
        "connect-src 'self'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
    ]
)

# Rotas livres do rate limit: verificação de saúde e arquivos estáticos.
# A comparação precisa considerar prefixo, porque os arquivos servidos são
# /static/css/style.css, /static/js/app.js e assim por diante.
PREFIXOS_LIVRES = ("/static",)
CAMINHOS_LIVRES = frozenset({"/saude"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
        if get_settings().app_env == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))[:128]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        caminho = request.url.path
        if caminho in CAMINHOS_LIVRES or caminho.startswith(PREFIXOS_LIVRES):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        key = f"{client}:{caminho}"
        now = time.monotonic()
        window = 60.0

        with self.lock:
            queue = self.requests[key]
            while queue and now - queue[0] > window:
                queue.popleft()
            if len(queue) >= settings.rate_limit_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Limite de requisições excedido. Tente novamente em instantes."},
                    headers={"Retry-After": "60"},
                )
            queue.append(now)
            # Sem esta limpeza o dicionário cresceria indefinidamente, guardando
            # uma chave para cada par IP+rota já visto desde que o processo subiu.
            if not queue:
                del self.requests[key]
            if len(self.requests) > 10_000:
                self._descartar_janelas_vazias(now, window)

        return await call_next(request)

    def _descartar_janelas_vazias(self, now: float, window: float) -> None:
        """Remove chaves cuja janela de contagem já expirou."""
        expiradas = [
            chave
            for chave, marcas in self.requests.items()
            if not marcas or now - marcas[-1] > window
        ]
        for chave in expiradas:
            del self.requests[chave]
