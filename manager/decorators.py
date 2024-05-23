# decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def permission_required_with_redirect(perm, login_url=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_perm(perm):
                if login_url:
                    return redirect(login_url)
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
