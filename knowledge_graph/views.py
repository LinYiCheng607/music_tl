from django.http import JsonResponse
from py2neo import Graph

def graph_data(request):
    # 连接Neo4j
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "your_password"))
    # 查询节点
    nodes = graph.run("MATCH (n) RETURN id(n) as id, labels(n) as labels, n.name as name LIMIT 100").data()
    # 查询关系
    edges = graph.run("MATCH (n)-[r]->(m) RETURN id(n) as source, id(m) as target, type(r) as label LIMIT 100").data()
    return JsonResponse({
        "nodes": nodes,
        "edges": edges
    })