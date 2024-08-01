from django.contrib import admin
from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('LittleLemonAPI.urls')),
    path('api/', include('djoser.urls')), 
    path('api/', include('djoser.urls.authtoken')),
    path('token/login/', obtain_auth_token),
]
# putting append slash false in settings makes it so you have to put a trailing slash??