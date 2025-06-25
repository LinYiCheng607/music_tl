from django.urls import path
from . import views

urlpatterns = [
    path('home/<int:page>.html', views.homeview, name='home'),
    path('login.html', views.loginview, name='login'),
    path('logout.html', views.logoutview, name='logout'),
    path('analysis/', views.song_analysis, name='song_analysis'),
    path('update_info/', views.update_user_info, name='update_user_info'),  # 新增
]
