from django.urls import path
from . import views

app_name = 'recommend'

urlpatterns = [
    path('songs/', views.recommend_songs, name='songs'),
]