"""
Post URL patterns.
Follows Django for Beginners Ch 5/6/13 URL patterns.
"""
from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    LikeToggleView,
    CommentCreateView,
    CommentDeleteView,
)

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("new/", PostCreateView.as_view(), name="post_new"),
    path("<int:pk>/", PostDetailView.as_view(), name="post_detail"),
    path("<int:pk>/edit/", PostUpdateView.as_view(), name="post_edit"),
    path("<int:pk>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("<int:pk>/like/", LikeToggleView.as_view(), name="post_like"),
    path("<int:post_pk>/comment/", CommentCreateView.as_view(), name="comment_new"),
    path(
        "comment/<int:pk>/delete/",
        CommentDeleteView.as_view(),
        name="comment_delete",
    ),
]
