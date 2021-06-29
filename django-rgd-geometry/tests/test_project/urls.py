from django.urls import include, path

urlpatterns = [
    # Make this distinct from typical production values, to ensure it works dynamically
    path('rgd_test/', include('rgd.urls')),
    path('rgd_geometry_test/', include('rgd_geometry.urls')),
]
