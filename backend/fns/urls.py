# fns/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # Add the new path
    path('test-firebase/', views.test_firebase_connection, name='test_firebase'),
    path('profile/', views.get_user_profile, name='get_user_profile'),
    path('upload-resume/', views.upload_resume_view, name='upload_resume'),
    path('upload-tex/', views.upload_tex_view, name='upload_tex'),
    path('resumes/<str:resume_id>/download/', views.download_resume_pdf_view, name='download_resume_pdf'),
]