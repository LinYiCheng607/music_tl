from django.urls import path
from . import views

urlpatterns = [
    path('<int:songid>.html', views.comment_view, name='comment'),
    path('review/<int:songid>/', views.song_review_view, name='song_review'),
]