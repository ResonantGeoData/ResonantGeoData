from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic.base import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/s3-upload/', include('s3_file_field.urls')),
    path('', include('rgd.urls')),
    path('', include('rgd_3d.urls')),
    path('', include('rgd_fmv.urls')),
    path('', include('rgd_geometry.urls')),
    path('', include('rgd_imagery.urls')),
    # Redirect homepage to RGD core app homepage
    path(r'', RedirectView.as_view(url='rgd', permanent=False), name='index'),
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
    re_path(
        r'^swagger(?P<format>\.json|\.yaml)$',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
