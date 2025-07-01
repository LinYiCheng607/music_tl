from django.urls import path
from . import views

urlpatterns = [
    path('', views.knowledge_graph2, name='knowledge_graph2'),  # 主页面
    path('search_kg/', views.knowledge_graph, name='search_kg'),  # 搜索页面
    path('search_kg/data/', views.get_graph_data, name='get_graph_data'),  # 新增，用于数据接口
    path('api/graph/', views.graph_data, name='graph_data'),
    path('api/graph_options/', views.graph_options, name='graph_options'),
    path('api/qa/', views.knowledge_graph_qa, name='knowledge_graph_qa'),
]