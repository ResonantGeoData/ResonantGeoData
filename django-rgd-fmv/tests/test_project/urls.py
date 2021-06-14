from django.urls import include, path

urlpatterns = [
    # Make this distinct from typical production values, to ensure it works dynamically
    path('rgd_test/', include('rgd.urls')),
    path('rgd_fmv_test/', include('rgd_fmv.urls')),
]
