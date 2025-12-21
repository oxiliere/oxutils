from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProfileListView.as_view(), name='profile_list'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/<int:pk>/pdf/', views.ProfilePDFView.as_view(), name='profile_pdf'),
    path('profile/<int:pk>/generate-cv/', views.generate_and_save_cv, name='generate_cv'),
    path('profile/<int:pk>/download-pdf/', views.download_standalone_pdf, name='download_pdf'),
]
