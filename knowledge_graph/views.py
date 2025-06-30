from django.shortcuts import render
from django.http import JsonResponse
from py2neo import Graph

def graph_options(request):
    kg_type = request.GET.get('type', 'artist-song')
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "2111601205"))

    if kg_type == 'artist-song':
        singers = graph.run("MATCH (si:Singer) RETURN si ORDER BY si.name LIMIT 100").data()
        relations = ["SUNG_BY"]
        return JsonResponse({
            "nodes": [{"id": str(s["si"].identity), "name": s["si"]["name"]} for s in singers],
            "relations": relations
        })
    elif kg_type == 'song-album':
        albums = graph.run("MATCH (al:Album) RETURN al ORDER BY al.name LIMIT 100").data()
        relations = ["IN_ALBUM"]
        return JsonResponse({
            "nodes": [{"id": str(a["al"].identity), "name": a["al"]["name"]} for a in albums],
            "relations": relations
        })
    elif kg_type == 'song-language':
        languages = graph.run("MATCH (l:Language) RETURN l ORDER BY l.name LIMIT 100").data()
        relations = ["IN_LANGUAGE"]
        return JsonResponse({
            "nodes": [{"id": str(l["l"].identity), "name": l["l"]["name"]} for l in languages],
            "relations": relations
        })
    elif kg_type == 'song-type':
        types = graph.run("MATCH (t:Type) RETURN t ORDER BY t.name LIMIT 100").data()
        relations = ["BELONGS_TO"]
        return JsonResponse({
            "nodes": [{"id": str(t["t"].identity), "name": t["t"]["name"]} for t in types],
            "relations": relations
        })
    else:
        return JsonResponse({"nodes": [], "relations": []})

def graph_data(request):
    kg_type = request.GET.get('type', 'artist-song')
    node_id = request.GET.get('node_id')
    relation = request.GET.get('relation')
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "2111601205"))

    nodes = []
    edges = []

    LIMIT = 100  # 限制节点数量

    if kg_type == 'artist-song' and node_id and relation == "SUNG_BY":
        singer = graph.run("MATCH (si:Singer) WHERE id(si)=$sid RETURN si", sid=int(node_id)).evaluate()
        if singer:
            nodes.append({'id': str(singer.identity), 'labels': list(singer.labels), 'name': singer.get('name', '')})
            # 查询该歌手的所有歌曲及SUNG_BY关系
            songs = graph.run(
                f"""
                MATCH (song:Song)-[r:SUNG_BY]->(si:Singer)
                WHERE id(si)=$sid
                RETURN song, r
                LIMIT {LIMIT}
                """, sid=int(node_id)
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(singer.identity), 'label': 'SUNG_BY'})
    elif kg_type == 'song-album' and node_id and relation == "IN_ALBUM":
        album = graph.run("MATCH (al:Album) WHERE id(al)=$aid RETURN al", aid=int(node_id)).evaluate()
        if album:
            nodes.append({'id': str(album.identity), 'labels': list(album.labels), 'name': album.get('name', '')})
            # 查询该专辑的所有歌曲及IN_ALBUM关系
            songs = graph.run(
                f"""
                MATCH (song:Song)-[r:IN_ALBUM]->(al:Album)
                WHERE id(al)=$aid
                RETURN song, r
                LIMIT {LIMIT}
                """, aid=int(node_id)
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(album.identity), 'label': 'IN_ALBUM'})
    elif kg_type == 'song-language' and node_id and relation == "IN_LANGUAGE":
        language = graph.run("MATCH (l:Language) WHERE id(l)=$lid RETURN l", lid=int(node_id)).evaluate()
        if language:
            nodes.append({'id': str(language.identity), 'labels': list(language.labels), 'name': language.get('name', '')})
            # 查询该语言的所有歌曲及IN_LANGUAGE关系
            songs = graph.run(
                f"""
                MATCH (song:Song)-[r:IN_LANGUAGE]->(l:Language)
                WHERE id(l)=$lid
                RETURN song, r
                LIMIT {LIMIT}
                """, lid=int(node_id)
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(language.identity), 'label': 'IN_LANGUAGE'})

    # 去重
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n['id'] not in seen:
            seen.add(n['id'])
            unique_nodes.append(n)
    nodes = unique_nodes

    # 限制节点数量（如加 LIMIT 还不够保险）
    if len(nodes) > LIMIT:
        nodes = nodes[:LIMIT]
        node_ids = set(n['id'] for n in nodes)
        # 只保留与这些节点相关的边
        edges = [e for e in edges if e['source'] in node_ids and e['target'] in node_ids]

    return JsonResponse({
        "nodes": nodes,
        "edges": edges
    })

def knowledge_graph(request):
    return render(request, 'knowledge_graph.html')