from django.urls import include, path

urlpatterns = [
    # Make this distinct from typical production values, to ensure it works dynamically
    path('', include('rgd.urls')),
    path('', include('rgd_imagery.urls')),
]
