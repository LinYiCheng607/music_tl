from django.urls import path
from . import views

app_name = 'aiassistant'

urlpatterns = [
    path('', views.assistant_page, name='assistant_page'),
    path('chat/', views.chat_with_assistant, name='chat'),
] 