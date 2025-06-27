from django.urls import path
from . import views

urlpatterns = [
    path('<int:songid>.html', views.comment_view, name='comment'),
]