from django.urls import path

from . import views

app_name = 'comments'

urlpatterns = [
    path('<int:pk>/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),
    path('<int:pk>/edit/', views.CommentEditView.as_view(), name='comment_edit'),
]
