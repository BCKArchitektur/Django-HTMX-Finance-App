from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):
    """
    DRF authentication class for external app integrations.

    Expects the header:
        Authorization: Api-Key <key>

    Returns (None, api_key_instance) on success so that DRF marks the
    request as authenticated without associating it with a Django user.
    Raises AuthenticationFailed if the header is present but the key is
    invalid or inactive — does NOT silently fall through in that case.
    Returns None (unauthenticated, pass to next authenticator) if the
    Authorization header is absent or uses a different scheme.
    """

    def authenticate(self, request):
        from .models import APIKey  # local import avoids circular import at module load

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Api-Key '):
            return None  # not our scheme — let other authenticators handle it

        raw_key = auth_header[len('Api-Key '):]
        try:
            api_key = APIKey.objects.get(key=raw_key, is_active=True)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid or inactive API key.')

        return (None, api_key)

    def authenticate_header(self, request):
        # Tells DRF what to put in the WWW-Authenticate header on 401 responses
        return 'Api-Key realm="api"'
