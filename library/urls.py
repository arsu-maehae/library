from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('librarian/', include('librarian.urls')),
    path('', include('member.urls')),
]
