from django.urls import path

from . import views

app_name = "posts"

urlpatterns = [
    path("new/", views.PostCreateView.as_view(), name="post_create"),
    path("tags/", views.TrendingTagsView.as_view(), name="trending_tags"),
    path("tags/<slug:slug>/", views.HashtagDetailView.as_view(), name="hashtag_detail"),
    path("<int:pk>/", views.PostDetailView.as_view(), name="post_detail"),
    path("<int:pk>/edit/", views.PostUpdateView.as_view(), name="post_update"),
    path("<int:pk>/delete/", views.PostDeleteView.as_view(), name="post_delete"),
    path("<int:pk>/save/", views.PostSaveView.as_view(), name="post_save"),
    path("<int:pk>/share/", views.SharePostView.as_view(), name="post_share"),
    path("saved/", views.SavedPostListView.as_view(), name="saved_posts"),
    path(
        "collections/create/",
        views.CollectionCreateView.as_view(),
        name="collection_create",
    ),
    path(
        "collections/<int:pk>/",
        views.CollectionDetailView.as_view(),
        name="collection_detail",
    ),
    path(
        "collections/<int:pk>/delete/",
        views.CollectionDeleteView.as_view(),
        name="collection_delete",
    ),
]
