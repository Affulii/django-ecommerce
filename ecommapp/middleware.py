# ecommapp/middleware.py
import logging
from .models import UserLog

logger = logging.getLogger('ecommapp')

class AutomaticActivityLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code executed before the view is called
        response = self.get_response(request)
        # Code executed after the view is called

        # Automatically log HTTP errors (4xx and 5xx) across ALL pages
        if response.status_code >= 400:
            ip = request.META.get('REMOTE_ADDR')
            user = request.user if request.user.is_authenticated else None
            
            # Log to DB
            UserLog.objects.create(
                user=user,
                action=f"HTTP {response.status_code} Error on {request.path}",
                details=f"Method: {request.method}",
                log_level='ERROR' if response.status_code >= 500 else 'WARNING',
                ip_address=ip
            )
            
            # Log to File
            logger.error(f"User {user} hit {response.status_code} on {request.path}")

        return response