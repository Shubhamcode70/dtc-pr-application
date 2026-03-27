"""
Request logging middleware for audit trail
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from apps.audit.models import AuditLog

logger = logging.getLogger('audit')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all HTTP requests for audit purposes"""
    
    def get_client_ip(self, request):
        """Get client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def process_request(self, request):
        """Log incoming request"""
        # Store IP and user agent for response logging
        request._audit_ip = self.get_client_ip(request)
        request._audit_user_agent = request.META.get('HTTP_USER_AGENT', '')
        return None
    
    def process_response(self, request, response):
        """Log outgoing response"""
        # Skip logging for static files and media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
        
        # Skip logging for admin list views (too noisy)
        if request.path.startswith('/admin/') and request.method == 'GET':
            return response
        
        # Log important requests
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            try:
                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='other',
                    model_name=request.path.split('/')[-2],
                    object_id='',
                    description=f"{request.method} {request.path}",
                    ip_address=request._audit_ip,
                    user_agent=request._audit_user_agent[:500],
                    success=response.status_code < 400,
                )
            except Exception as e:
                logger.error(f"Error logging request: {e}")
        
        return response
