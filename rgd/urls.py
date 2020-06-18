from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
import uritemplate  # noqa: F401


urlpatterns = [
    path('', include('core.urls')),
    path('', include('geodata.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
]

schema_view = get_schema_view(
    openapi.Info(
        title='ResonantGeoData API',
        default_version='v1',
        description='ResonantGeoData',
        # terms_of_service='https://www.google.com/policies/terms/',
        contact=openapi.Contact(email='kitware@kitare.com'),
        license=openapi.License(name='Apache 2.0'),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    patterns=urlpatterns,
)

urlpatterns += [
    url(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
