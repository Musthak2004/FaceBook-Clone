from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('new/', views.PostCreateView.as_view(), name='post_create'),
    path('<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('<int:pk>/save/', views.PostSaveView.as_view(), name='post_save'),
]
