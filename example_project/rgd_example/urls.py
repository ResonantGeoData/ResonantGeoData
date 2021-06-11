from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    # path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    # path('api/s3-upload/', include('s3_file_field.urls')),
    path('', include('rgd.urls')),
]
