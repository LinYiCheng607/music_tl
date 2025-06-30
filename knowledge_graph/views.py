from django.shortcuts import render
from django.http import JsonResponse
from py2neo import Graph

def graph_data(request):
    kg_type = request.GET.get('type', 'artist-song')
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "2111601205"))

    if kg_type == 'artist-song':
        # 只选前20个歌手，每个歌手前10首歌
        nodes = []
        edges = []
        singers = graph.run("MATCH (si:Singer) RETURN si LIMIT 20").data()
        singer_ids = []
        for s in singers:
            si = s['si']
            singer_ids.append(si.identity)
            nodes.append({'id': str(si.identity), 'labels': list(si.labels), 'name': si.get('name', '')})
            # 获取该歌手的前10首歌
            songs = graph.run(
                "MATCH (song:Song)-[r:SUNG_BY]->(si:Singer) WHERE id(si)=$sid RETURN song, r LIMIT 10",
                sid=si.identity
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(si.identity), 'label': r.__class__.__name__ if hasattr(r, '__class__') else 'SUNG_BY'})
    elif kg_type == 'song-album':
        nodes = []
        edges = []
        albums = graph.run("MATCH (al:Album) RETURN al LIMIT 20").data()
        for a in albums:
            al = a['al']
            nodes.append({'id': str(al.identity), 'labels': list(al.labels), 'name': al.get('name', '')})
            songs = graph.run(
                "MATCH (song:Song)-[r:IN_ALBUM]->(al:Album) WHERE id(al)=$aid RETURN song, r LIMIT 10",
                aid=al.identity
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(al.identity), 'label': r.__class__.__name__ if hasattr(r, '__class__') else 'IN_ALBUM'})
    elif kg_type == 'song-language':
        nodes = []
        edges = []
        languages = graph.run("MATCH (l:Language) RETURN l LIMIT 10").data()
        for litem in languages:
            l = litem['l']
            nodes.append({'id': str(l.identity), 'labels': list(l.labels), 'name': l.get('name', '')})
            songs = graph.run(
                "MATCH (song:Song)-[r:IN_LANGUAGE]->(l:Language) WHERE id(l)=$lid RETURN song, r LIMIT 10",
                lid=l.identity
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(l.identity), 'label': r.__class__.__name__ if hasattr(r, '__class__') else 'IN_LANGUAGE'})
    else:
        nodes = []
        edges = []

    # 去重
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n['id'] not in seen:
            seen.add(n['id'])
            unique_nodes.append(n)
    nodes = unique_nodes

    return JsonResponse({
        "nodes": nodes,
        "edges": edges
    })

def knowledge_graph(request):
    return render(request, 'knowledge_graph.html')