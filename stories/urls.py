from django.urls import path

from . import views

app_name = "stories"

urlpatterns = [
    path("", views.StoryListView.as_view(), name="list"),
    path("upload/", views.StoryUploadView.as_view(), name="upload"),
    path("row/", views.StoriesRowView.as_view(), name="row"),
]
