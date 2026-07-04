from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeFeedView.as_view(), name='home'),
]
