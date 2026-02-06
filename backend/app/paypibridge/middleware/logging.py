"""
Structured logging middleware for PayPiBridge.
Adds request IDs and structured logging to all requests.
"""
import uuid
import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware that adds a unique request ID to each request.
    The request ID is available in request.request_id and logged in all log entries.
    """
    
    def process_request(self, request):
        """Add request ID to request."""
        # Get request ID from header if present, otherwise generate one
        request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))
        request.request_id = request_id
        
        # Add to META for logging
        request.META['REQUEST_ID'] = request_id
        
        return None


class StructuredLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs structured information about each request.
    Logs request start, end, duration, status code, and user info.
    """
    
    def process_request(self, request):
        """Log request start."""
        request._start_time = time.time()
        
        # Get request ID (set by RequestIDMiddleware)
        request_id = getattr(request, 'request_id', 'unknown')
        
        # Log request start
        logger.info(
            "Request started",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'user': getattr(request.user, 'username', 'anonymous') if hasattr(request, 'user') else 'anonymous',
                'ip': self._get_client_ip(request),
            }
        )
        
        return None
    
    def process_response(self, request, response):
        """Log request completion."""
        # Calculate duration
        duration = None
        if hasattr(request, '_start_time'):
            duration = (time.time() - request._start_time) * 1000  # Convert to milliseconds
        
        # Get request ID
        request_id = getattr(request, 'request_id', 'unknown')
        
        # Log request completion
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        
        logger.log(
            log_level,
            "Request completed",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration, 2) if duration else None,
                'user': getattr(request.user, 'username', 'anonymous') if hasattr(request, 'user') else 'anonymous',
                'ip': self._get_client_ip(request),
            }
        )
        
        # Add request ID to response header
        response['X-Request-ID'] = request_id
        
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions."""
        request_id = getattr(request, 'request_id', 'unknown')
        
        logger.error(
            "Request exception",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'user': getattr(request.user, 'username', 'anonymous') if hasattr(request, 'user') else 'anonymous',
                'ip': self._get_client_ip(request),
            },
            exc_info=True
        )
        
        return None
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
