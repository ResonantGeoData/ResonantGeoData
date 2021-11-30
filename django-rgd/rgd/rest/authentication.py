from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions


class UserSigner:
    """Signs/unsigns user object with an expiry."""

    signer_class = signing.TimestampSigner

    def sign(self, user):
        signer = self.signer_class()
        data = {'user_id': user.pk, 'username': user.get_username()}
        return signer.sign(signing.dumps(data))

    def unsign(self, signature, max_age=None):
        max_age = getattr(settings, 'RGD_SIGNED_URL_TTL', None)
        if max_age is None:
            max_age = 60 * 60 * 24
        cls = get_user_model()
        signer = self.signer_class()
        data = signing.loads(signer.unsign(signature, max_age))
        if not isinstance(data, dict):
            raise signing.BadSignature()
        try:
            return cls.objects.get(
                **{'pk': data.get('user_id'), cls.USERNAME_FIELD: data.get('username')}
            )
        except cls.DoesNotExist:
            raise signing.BadSignature()


class SignedURLAuthentication:
    """
    Extend the TokenAuthentication class to support signed authentication.

    This takes the form of "http://www.example.com/?signature=<key>".
    """

    def authenticate(self, request):
        # Check if 'signature' is in the request query params.
        # Give precedence to 'Authorization' header.
        param_name = getattr(settings, 'RGD_SIGNED_URL_QUERY_PARAM', 'signature')
        if param_name in request.query_params and 'HTTP_AUTHORIZATION' not in request.META:
            if request.method != 'GET':
                raise exceptions.AuthenticationFailed(
                    _('Signatures are only allowed for GET requests.')
                )
            signer = UserSigner()
            sig = request.query_params.get(param_name)
            if not sig:
                return
            try:
                user = signer.unsign(sig)
            except signing.SignatureExpired:
                raise exceptions.AuthenticationFailed(_('The signature has expired.'))
            except signing.BadSignature:
                raise exceptions.AuthenticationFailed(_('Invalid signature.'))
            if not user.is_active:
                raise exceptions.AuthenticationFailed(_('Signing user is inactive or deleted.'))
            return (user, None)
