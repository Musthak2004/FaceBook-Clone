from django.urls import path

from . import views

app_name = "reactions"

urlpatterns = [
    path("<int:pk>/like/", views.PostLikeView.as_view(), name="post_like"),
]
