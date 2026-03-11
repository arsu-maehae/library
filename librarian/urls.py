from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.librarian_login, name='librarian_login'),
    path('logout/', views.admin_logout, name='logout'),
    path('manage/', views.manage_books, name='manage_books'),
    path('record/', views.active_borrows, name='active_borrows'),
    path('borrow/', views.borrow_process, name='borrow_process'),
    path('return/', views.return_book, name='return_book'),
    path('users/', views.manage_users, name='manage_users'),
    path('setting/', views.settings_view, name='settings_view'),
]