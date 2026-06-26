from django.contrib import admin
from django.urls import path, include  # <-- Added 'include' here

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),     # <-- Added this line to link your app!
]