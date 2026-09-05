import logging
import time

logger = logging.getLogger("deskhub.requests")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        user = getattr(request, "user", None)
        user_repr = user.username if (user and user.is_authenticated) else "anonymous"

        logger.info(
            "%s %s -> %s [%.1fms] user=%s",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
            user_repr,
        )
        return response


class CartCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        cart = request.session.get('cart', []) if hasattr(request, 'session') else []
        request.cart_count = len(cart)
        return self.get_response(request)