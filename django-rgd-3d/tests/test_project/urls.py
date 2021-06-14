from django.urls import include, path

urlpatterns = [
    # Make this distinct from typical production values, to ensure it works dynamically
    path('rgd_test/', include('rgd.urls')),
    path('rgd_3d_test/', include('rgd_3d.urls')),
]
