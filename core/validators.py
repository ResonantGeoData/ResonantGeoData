from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import magic


class MimetypeValidator(object):
    def __init__(self, mimetypes, message=None):
        self.mimetypes = mimetypes
        self.message = message

    def __call__(self, value):
        try:
            mime = magic.from_buffer(value.read(16384), mime=True)
        except AttributeError:
            raise ValidationError(
                _(self.message or 'Could not determine mimetype of %(value)s'),
                params={'value': value},
                code='invalid_mimetype')
        if not mime in self.mimetypes:
            raise ValidationError(
                self.message or _('%(value)s is not a file of mimetype %(mimetypes)s'),
                params={
                  'value': value,
                  'mimetypes': ', '.join(self.mimetypes)
                },
                code='invalid_mimetype')
