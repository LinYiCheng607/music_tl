from django.urls import path
from . import views

urlpatterns = [
    path('', views.knowledge_graph, name='knowledge_graph'),      # 页面
    path('api/graph/', views.graph_data, name='graph_data'),      # 数据API，注意最后带斜杠
]