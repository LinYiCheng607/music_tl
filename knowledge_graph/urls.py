from django.urls import path
from . import views
from index.views import indexview

urlpatterns = [
    path('', views.knowledge_graph, name='knowledge_graph'),      # 页面
    path('api/graph/', views.graph_data, name='graph_data'),      # 数据API
    path('api/graph_options/', views.graph_options, name='graph_options'),
    path('', indexview, name='index'),  
]