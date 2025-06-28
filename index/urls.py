from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.indexview),
    path('api/random_image', views.random_image, name='random_image'),
    path('recommend/', include('recommend.urls')),
]
