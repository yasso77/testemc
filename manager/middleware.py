from django.contrib.auth import logout
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

from manager.model.userExtra import UserExtra


class ForcePasswordChangeMiddleware:
    """After a successful login, block the app until the user sets a new password."""

    SESSION_KEY = 'password_change_pending'
    EXEMPT_PREFIXES = (
        '/password-change/',
        '/logout/',
        '/custom-logout-page/',
        '/accounts/login',
        '/login/',
        '/admin/login/',
        '/admin/logout/',
        '/static/',
        '/media/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is None or not user.is_authenticated:
            return self.get_response(request)

        if not self._must_change(user):
            request.session.pop(self.SESSION_KEY, None)
            return self.get_response(request)

        pending = request.session.get(self.SESSION_KEY)
        if not pending:
            # Old browser session: require a real login first.
            logout(request)
            return redirect('login')

        if not request.path.startswith(self.EXEMPT_PREFIXES):
            return redirect('password_change_forced')
        return self.get_response(request)

    def _must_change(self, user):
        try:
            extra = user.extra
        except (ObjectDoesNotExist, AttributeError):
            extra, _ = UserExtra.objects.get_or_create(
                user=user,
                defaults={'must_change_password': True},
            )
        return extra.must_change_password
