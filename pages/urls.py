from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.PageListView.as_view(), name="list"),
    path("create/", views.PageCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PageDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.PageUpdateView.as_view(), name="update"),
    path("<int:pk>/follow/", views.PageFollowView.as_view(), name="follow"),
    path("<int:pk>/post/", views.PagePostCreateView.as_view(), name="post"),
]
