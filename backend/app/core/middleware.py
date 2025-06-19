from fastapi import Request, Response,status
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis, max_requests: int, window_seconds: int):
        super().__init__(app)
        self.redis = redis
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        url_path = request.url.path
        redis_key = f"ratelimit:{client_ip}:{url_path}"
        logger.info(f"RateLimiter: {client_ip} accessing {url_path}")
        current_count = await self.redis.incr(redis_key)

        if current_count == 1:
            await self.redis.expire(redis_key, self.window_seconds)

        if current_count > self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip} on {url_path}")
            return Response(
                content="Too many requests. Please try again later.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        return await call_next(request)



# class CSRFMiddleware(BaseHTTPMiddleware):
#     def __init__(self, app, secret_key: str):
#         super().__init__(app)
#         self.secret_key = secret_key 

#     async def dispatch(self, request: Request, call_next):
#         if "csrf_token" not in request.session:
#             request.session["csrf_token"] = secrets.token_hex(16)

#         response = await call_next(request)
#         response.set_cookie(
#             key="csrf_token",
#             value=request.session["csrf_token"],
#             httponly=True,
#             secure=True,
#             samesite="Strict"
#         )
#         return response