from django.urls import path
from . import views

app_name = 'member'

urlpatterns = [
    # Serve the login page at root '/'
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_page'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
]
