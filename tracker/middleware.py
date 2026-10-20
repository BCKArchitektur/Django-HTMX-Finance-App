"""
Login-Pflicht fuer die gesamte App.

Bis 20.10.2026 hingen einzelne Views ohne @login_required im Netz (u. a.
Rechnungs-Download und Zahlung buchen). Diese Middleware verlangt fuer JEDE
Seite einen Login - auch fuer Views, die spaeter dazukommen.

Ausgenommen:
    /accounts/  Login/Logout (allauth)
    /admin/     hat einen eigenen Login
    /api/       externe API (HR-App), eigene Api-Key-Authentifizierung
    STATIC_URL  CSS/JS/Bilder (WhiteNoise liefert sie ohnehin vorher aus)
"""
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import JsonResponse

EXEMPT_PREFIXES = (
    '/accounts/',
    '/admin/',
    '/api/',
    '/' + settings.STATIC_URL.lstrip('/'),
)


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(EXEMPT_PREFIXES):
            # fetch/HTMX-Aufrufe bekommen 401 statt einer Login-Seite als "Antwort"
            if (request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                    or request.headers.get('HX-Request')
                    or 'application/json' in request.headers.get('Accept', '')):
                return JsonResponse({'error': 'Login erforderlich.'}, status=401)
            return redirect_to_login(request.get_full_path())
        return self.get_response(request)
