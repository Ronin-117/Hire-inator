# fns/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Add the new path
    path('test-firebase/', views.test_firebase_connection, name='test_firebase'),
    path('profile/', views.get_user_profile, name='get_user_profile'),
]