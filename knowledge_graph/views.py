from django.shortcuts import render
from django.http import JsonResponse
from py2neo import Graph
from django.views.decorators.csrf import csrf_exempt
from index.models import Song  # 按你的实际模型调整
import openai
import json
import re

MOONSHOT_API_KEY = "sk-8AuZH3edVbJxU0l5zXhcCCU8BJX4fhLELtNkyE0XQzI1ptgF"

def graph_options(request):
    kg_type = request.GET.get('type', 'artist-song')
    graph = Graph("bolt://206.237.119.211:7687", auth=("neo4j", "2111601205"))

    if kg_type == 'artist-song':
        singers = graph.run("MATCH (si:Singer) RETURN si ORDER BY si.name").data()
        relations = ["SUNG_BY"]
        return JsonResponse({
            "nodes": [{"id": str(s["si"].identity), "name": s["si"]["name"]} for s in singers],
            "relations": relations
        })
    elif kg_type == 'song-album':
        albums = graph.run("MATCH (al:Album) RETURN al ORDER BY al.name").data()
        relations = ["IN_ALBUM"]
        return JsonResponse({
            "nodes": [{"id": str(a["al"].identity), "name": a["al"]["name"]} for a in albums],
            "relations": relations
        })
    elif kg_type == 'song-language':
        languages = graph.run("MATCH (l:Language) RETURN l ORDER BY l.name").data()
        relations = ["IN_LANGUAGE"]
        return JsonResponse({
            "nodes": [{"id": str(l["l"].identity), "name": l["l"]["name"]} for l in languages],
            "relations": relations
        })
    elif kg_type == 'song-type':
        types = graph.run("MATCH (t:Type) RETURN t ORDER BY t.name").data()
        relations = ["BELONGS_TO"]
        return JsonResponse({
            "nodes": [{"id": str(t["t"].identity), "name": t["t"]["name"]} for t in types],
            "relations": relations
        })
    elif kg_type == 'artist-album':
        # 歌手-专辑：返回歌手列表和专辑列表
        singers = graph.run("MATCH (si:Singer) RETURN si ORDER BY si.name").data()
        albums = graph.run("MATCH (al:Album) RETURN al ORDER BY al.name").data()
        relations = ["PUBLISH_ALBUM"]
        return JsonResponse({
            "nodes": [{"id": str(s["si"].identity), "name": s["si"]["name"]} for s in singers],
            "albums": [{"id": str(a["al"].identity), "name": a["al"]["name"]} for a in albums],
            "relations": relations
        })
    else:
        return JsonResponse({"nodes": [], "relations": []})

def graph_data(request):
    kg_type = request.GET.get('type', 'artist-song')
    node_id = request.GET.get('node_id')
    relation = request.GET.get('relation')
    album_id = request.GET.get('album_id', '')
    graph = Graph("bolt://206.237.119.211:7687", auth=("neo4j", "2111601205"))

    nodes = []
    edges = []
    LIMIT = 100

    if kg_type == 'artist-song' and node_id and relation == "SUNG_BY":
        singer = graph.run("MATCH (si:Singer) WHERE id(si)=$sid RETURN si", sid=int(node_id)).evaluate()
        if singer:
            nodes.append({'id': str(singer.identity), 'labels': list(singer.labels), 'name': singer.get('name', '')})
            songs = graph.run(
                """
                MATCH (song:Song)-[r:SUNG_BY]->(si:Singer)
                WHERE id(si)=$sid
                RETURN song, r
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
            songs = graph.run(
                """
                MATCH (song:Song)-[r:IN_ALBUM]->(al:Album)
                WHERE id(al)=$aid
                RETURN song, r
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
            songs = graph.run(
                """
                MATCH (song:Song)-[r:IN_LANGUAGE]->(l:Language)
                WHERE id(l)=$lid
                RETURN song, r
                """, lid=int(node_id)
            ).data()
            for item in songs:
                song = item['song']
                r = item['r']
                nodes.append({'id': str(song.identity), 'labels': list(song.labels), 'name': song.get('name', '')})
                edges.append({'source': str(song.identity), 'target': str(language.identity), 'label': 'IN_LANGUAGE'})
    elif kg_type == 'artist-album' and node_id and relation == "PUBLISH_ALBUM":
        singer = graph.run("MATCH (si:Singer) WHERE id(si)=$sid RETURN si", sid=int(node_id)).evaluate()
        if singer:
            nodes.append({'id': str(singer.identity), 'labels': list(singer.labels), 'name': singer.get('name', '')})
            if album_id:
                album = graph.run("MATCH (al:Album) WHERE id(al)=$aid RETURN al", aid=int(album_id)).evaluate()
                if album:
                    nodes.append({'id': str(album.identity), 'labels': list(album.labels), 'name': album.get('name', '')})
                    edges.append({'source': str(singer.identity), 'target': str(album.identity), 'label': 'PUBLISH_ALBUM'})
            else:
                # 修正：查真实的 PUBLISH_ALBUM 关系
                albums = graph.run(
                    """
                    MATCH (si:Singer)-[:PUBLISH_ALBUM]->(al:Album)
                    WHERE id(si)=$sid
                    RETURN al
                    """, sid=int(node_id)
                ).data()
                for item in albums:
                    album = item['al']
                    nodes.append({'id': str(album.identity), 'labels': list(album.labels), 'name': album.get('name', '')})
                    edges.append({'source': str(singer.identity), 'target': str(album.identity), 'label': 'PUBLISH_ALBUM'})

    # 去重
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n['id'] not in seen:
            seen.add(n['id'])
            unique_nodes.append(n)
    nodes = unique_nodes

    if len(nodes) > LIMIT:
        nodes = nodes[:LIMIT]
        node_ids = set(n['id'] for n in nodes)
        edges = [e for e in edges if e['source'] in node_ids and e['target'] in node_ids]

    return JsonResponse({
        "nodes": nodes,
        "edges": edges
    })

def knowledge_graph2(request):
    return render(request, 'knowledge_graph.html')

def search_kg(request):
    return render(request, 'search_kg.html')

def query_llm(question, history=None):
    prompt = f"""你是一个音乐知识图谱问答助手。
请严格只输出如下格式的JSON，不要输出多余内容，不要加markdown代码块标记，不要加解释：
{{"intent": "...", "singer": "...", "song": "...", "album": "...", "language": "...", "type": "..."}}。
如果没有提及的项请填 null。
用户输入：{question}
"""
    try:
        client = openai.OpenAI(
            api_key=MOONSHOT_API_KEY,
            base_url="https://api.moonshot.cn/v1"
        )
        completion = client.chat.completions.create(
            model="moonshot-v1-8k",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        reply = completion.choices[0].message.content
        print("moonshot content:", reply)
        reply = reply.strip()
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            reply = match.group()
        info = json.loads(reply)
        print("moonshot parsed:", info)
        return info
    except Exception as e:
        print("解析moonshot失败：", e)
        return None

def intent_match(intent, expected):
    if not intent:
        return False
    if isinstance(expected, str):
        expected = [expected]
    for e in expected:
        if e in intent or intent in e:
            return True
    return False

@csrf_exempt
def knowledge_graph_qa(request):
    if request.method != "POST":
        return JsonResponse({'error': '仅支持POST'}, status=405)
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        history = data.get('history', [])

        if not question:
            return JsonResponse({'error': '问题不能为空'}, status=400)
        info = query_llm(question, history)
        if not info:
            return JsonResponse({'error': '大模型理解失败，请换种问法'}, status=400)

        intent = info.get("intent", "")
        singer = info.get("singer")
        song = info.get("song")
        album = info.get("album")
        language = info.get("language")
        song_type = info.get("type")

        print("LLM返回：", info)
        print("intent:", intent, "singer:", singer, "song:", song, "album:", album)

        graph = Graph("bolt://206.237.119.211:7687", auth=("neo4j", "2111601205"))

        # 1. 某歌手有哪些专辑
        if singer and (
            intent_match(intent, [
                "query_albums_by_artist", "query_albums", "artist_album", 
                "albums", "query_artist_album", "query_album_by_artist", 
                "singer_album", "singer_albums", "get_albums", "歌手专辑", "专辑"
            ]) 
            or "album" in (intent or "") 
            or "专辑" in (intent or "")
        ):
            singer_node = graph.nodes.match("Singer", name=singer).first()
            if not singer_node:
                return JsonResponse({'error': f'未找到歌手：{singer}'}, status=404)
            albums = graph.run(
                """
                MATCH (si:Singer)-[:PUBLISH_ALBUM]->(al:Album)
                WHERE id(si)=$sid
                RETURN al
                """, sid=singer_node.identity
            ).data()
            if not albums:
                return JsonResponse({'error': f'未找到歌手：{singer} 的专辑信息'}, status=404)
            nodes = [{
                'id': str(singer_node.identity),
                'name': singer,
                'labels': list(singer_node.labels),
                'desc': f'歌手：{singer}'
            }]
            edges = []
            for item in albums:
                album_obj = item['al']
                nodes.append({
                    'id': str(album_obj.identity),
                    'name': album_obj.get('name', ''),
                    'labels': list(album_obj.labels),
                    'desc': f'专辑：{album_obj.get("name", "")}'
                })
                edges.append({
                    'source': str(singer_node.identity),
                    'target': str(album_obj.identity),
                    'label': 'PUBLISH_ALBUM',
                    'desc': f'{singer}发行专辑'
                })
            desc = f"{singer}共发行{len(albums)}张专辑：" + "、".join([item['al']['name'] for item in albums[:10]]) + ("..." if len(albums) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 2. 某歌手有哪些歌曲
        if singer and (
            intent_match(intent, [
                "query_songs_by_artist", "query_songs", "artist_song", 
                "songs", "get_songs", "歌手歌曲", "歌曲"
            ])
            or "song" in (intent or "")
            or "歌曲" in (intent or "")
        ):
            singer_node = graph.nodes.match("Singer", name=singer).first()
            if not singer_node:
                return JsonResponse({'error': f'未找到歌手：{singer}'}, status=404)
            nodes = [{
                'id': str(singer_node.identity),
                'name': singer,
                'labels': list(singer_node.labels),
                'desc': f'歌手：{singer}'
            }]
            edges = []
            songs = graph.run(
                """
                MATCH (song:Song)-[:SUNG_BY]->(si:Singer)
                WHERE id(si)=$sid
                RETURN song
                """, sid=singer_node.identity
            ).data()
            for item in songs:
                song_obj = item['song']
                nodes.append({
                    'id': str(song_obj.identity),
                    'name': song_obj.get('name', ''),
                    'labels': list(song_obj.labels),
                    'desc': f'歌曲：{song_obj.get("name", "")}'
                })
                edges.append({
                    'source': str(song_obj.identity),
                    'target': str(singer_node.identity),
                    'label': 'SUNG_BY',
                    'desc': f'{singer}演唱'
                })
            desc = f"{singer}共收录{len(songs)}首歌曲：" + "、".join([item['song']['name'] for item in songs[:10]]) + ("..." if len(songs) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 3. 某歌曲属于哪个专辑
        if song and (
            intent_match(intent, [
                "query_album_by_song", "song_album", "get_album_by_song", 
                "歌曲专辑", "专辑", "album"
            ])
            or ("专辑" in (intent or "") and "歌曲" in (intent or ""))
            or ("album" in (intent or "") and "song" in (intent or ""))
        ):
            song_node = graph.nodes.match("Song", name=song).first()
            if not song_node:
                return JsonResponse({'error': f'未找到歌曲：{song}'}, status=404)
            album_rel = graph.run(
                """
                MATCH (song:Song)-[:IN_ALBUM]->(al:Album)
                WHERE id(song)=$sid
                RETURN al
                """, sid=song_node.identity
            ).evaluate()
            nodes = [
                {'id': str(song_node.identity), 'name': song, 'labels': list(song_node.labels), 'desc': f'歌曲：{song}'}
            ]
            edges = []
            if album_rel:
                nodes.append({'id': str(album_rel.identity), 'name': album_rel.get('name', ''), 'labels': list(album_rel.labels), 'desc': f'专辑：{album_rel.get("name", "")}'})
                edges.append({'source': str(song_node.identity), 'target': str(album_rel.identity), 'label': 'IN_ALBUM', 'desc': '属于专辑'})
                desc = f"《{song}》属于专辑《{album_rel.get('name', '')}》"
            else:
                desc = f"未找到《{song}》的专辑信息"
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 4. 某专辑有哪些歌曲
        if album and (
            intent_match(intent, [
                "query_songs_by_album", "album_songs", "get_songs_by_album", 
                "专辑歌曲", "歌曲", "songs"
            ])
            or ("专辑" in (intent or "") and "歌曲" in (intent or ""))
            or ("album" in (intent or "") and "song" in (intent or ""))
        ):
            album_node = graph.nodes.match("Album", name=album).first()
            if not album_node:
                return JsonResponse({'error': f'未找到专辑：{album}'}, status=404)
            songs = graph.run(
                """
                MATCH (song:Song)-[:IN_ALBUM]->(al:Album)
                WHERE id(al)=$aid
                RETURN song
                """, aid=album_node.identity
            ).data()
            nodes = [{
                'id': str(album_node.identity),
                'name': album,
                'labels': list(album_node.labels),
                'desc': f'专辑：{album}'
            }]
            edges = []
            for item in songs:
                song_obj = item['song']
                nodes.append({
                    'id': str(song_obj.identity),
                    'name': song_obj.get('name', ''),
                    'labels': list(song_obj.labels),
                    'desc': f'歌曲：{song_obj.get("name", "")}'
                })
                edges.append({
                    'source': str(album_node.identity),
                    'target': str(song_obj.identity),
                    'label': 'IN_ALBUM',
                    'desc': f'专辑收录'
                })
            desc = f"专辑《{album}》收录{len(songs)}首歌曲：" + "、".join([item['song']['name'] for item in songs[:10]]) + ("..." if len(songs) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 5. 某歌曲的语种
        if song and (
            intent_match(intent, [
                "query_language_by_song", "song_language", "get_language_by_song", 
                "歌曲语种", "语种", "language"
            ])
            or "language" in (intent or "")
            or "语种" in (intent or "")
        ):
            song_node = graph.nodes.match("Song", name=song).first()
            if not song_node:
                return JsonResponse({'error': f'未找到歌曲：{song}'}, status=404)
            lang_rel = graph.run(
                """
                MATCH (song:Song)-[:IN_LANGUAGE]->(lang:Language)
                WHERE id(song)=$sid
                RETURN lang
                """, sid=song_node.identity
            ).evaluate()
            nodes = [
                {'id': str(song_node.identity), 'name': song, 'labels': list(song_node.labels), 'desc': f'歌曲：{song}'}
            ]
            edges = []
            if lang_rel:
                nodes.append({'id': str(lang_rel.identity), 'name': lang_rel.get('name', ''), 'labels': list(lang_rel.labels), 'desc': f'语种：{lang_rel.get("name", "")}'})
                edges.append({'source': str(song_node.identity), 'target': str(lang_rel.identity), 'label': 'IN_LANGUAGE', 'desc': '语种'})
                desc = f"《{song}》的语种为：{lang_rel.get('name', '')}"
            else:
                desc = f"未找到《{song}》的语种信息"
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 6. 某类型有哪些歌曲
        if song_type and (
            intent_match(intent, [
                "query_songs_by_type", "type_songs", "get_songs_by_type", 
                "类型歌曲", "songs", "type"
            ])
            or "type" in (intent or "")
            or "类型" in (intent or "")
        ):
            type_node = graph.nodes.match("Type", name=song_type).first()
            if not type_node:
                return JsonResponse({'error': f'未找到类型：{song_type}'}, status=404)
            songs = graph.run(
                """
                MATCH (song:Song)-[:BELONGS_TO]->(t:Type)
                WHERE id(t)=$tid
                RETURN song
                """, tid=type_node.identity
            ).data()
            nodes = [{
                'id': str(type_node.identity),
                'name': song_type,
                'labels': list(type_node.labels),
                'desc': f'类型：{song_type}'
            }]
            edges = []
            for item in songs:
                song_obj = item['song']
                nodes.append({
                    'id': str(song_obj.identity),
                    'name': song_obj.get('name', ''),
                    'labels': list(song_obj.labels),
                    'desc': f'歌曲：{song_obj.get("name", "")}'
                })
                edges.append({
                    'source': str(type_node.identity),
                    'target': str(song_obj.identity),
                    'label': 'BELONGS_TO',
                    'desc': f'属于类型'
                })
            desc = f"{song_type}类型共收录{len(songs)}首歌曲：" + "、".join([item['song']['name'] for item in songs[:10]]) + ("..." if len(songs) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 7. 这首歌是谁唱的
        if song and (
            intent_match(intent, [
                "query_artist_by_song", "song_artist", "get_artist_by_song", 
                "歌曲歌手", "演唱者", "歌手", "artist"
            ])
            or "artist" in (intent or "")
            or "歌手" in (intent or "")
        ):
            song_node = graph.nodes.match("Song", name=song).first()
            if not song_node:
                return JsonResponse({'error': f'未找到歌曲：{song}'}, status=404)
            singer_rel = graph.run(
                """
                MATCH (song:Song)-[:SUNG_BY]->(si:Singer)
                WHERE id(song)=$sid
                RETURN si
                """, sid=song_node.identity
            ).evaluate()
            nodes = [
                {'id': str(song_node.identity), 'name': song, 'labels': list(song_node.labels), 'desc': f'歌曲：{song}'}
            ]
            edges = []
            if singer_rel:
                nodes.append({'id': str(singer_rel.identity), 'name': singer_rel.get('name', ''), 'labels': list(singer_rel.labels), 'desc': f'歌手：{singer_rel.get("name", "")}'})
                edges.append({'source': str(singer_rel.identity), 'target': str(song_node.identity), 'label': 'SUNG_BY', 'desc': f'演唱'})
                desc = f"《{song}》是由{singer_rel.get('name', '')}演唱"
            else:
                desc = f"未找到《{song}》的歌手信息"
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 8. 这首歌是什么类型
        if song and (
            intent_match(intent, [
                "query_type_by_song", "song_type", "type", "query_type", 
                "query_music_type", "get_type_by_song", "歌曲类型", "类型"
            ])
            or "type" in (intent or "")
            or "类型" in (intent or "")
        ):
            song_node = graph.nodes.match("Song", name=song).first()
            if not song_node:
                return JsonResponse({'error': f'未找到歌曲：{song}'}, status=404)
            type_rel = graph.run(
                """
                MATCH (song:Song)-[:BELONGS_TO]->(t:Type)
                WHERE id(song)=$sid
                RETURN t
                """, sid=song_node.identity
            ).evaluate()
            nodes = [
                {'id': str(song_node.identity), 'name': song, 'labels': list(song_node.labels), 'desc': f'歌曲：{song}'}
            ]
            edges = []
            if type_rel:
                nodes.append({'id': str(type_rel.identity), 'name': type_rel.get('name', ''), 'labels': list(type_rel.labels), 'desc': f'类型：{type_rel.get("name", "")}'})
                edges.append({'source': str(song_node.identity), 'target': str(type_rel.identity), 'label': 'BELONGS_TO', 'desc': '属于类型'})
                desc = f"《{song}》的类型为：{type_rel.get('name', '')}"
            else:
                desc = f"未找到《{song}》的类型信息"
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        return JsonResponse({'error': '暂不支持此类问题'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'解析失败: {e}'}, status=500)

def knowledge_graph(request):
    return render(request, 'search_knowledge_graph/graph.html')

def get_graph_data(request):
    song_name = request.GET.get('song_name', '')
    singer = request.GET.get('singer', '')
    album = request.GET.get('album', '')
    language = request.GET.get('language', '')
    release = request.GET.get('release', '')

    filters = {}
    if song_name:
        filters['song_name__icontains'] = song_name
    if singer:
        filters['song_singer__icontains'] = singer
    if album:
        filters['song_album__icontains'] = album
    if language:
        filters['song_languages__icontains'] = language
    if release:
        filters['song_release__icontains'] = release

    songs = Song.objects.filter(**filters) if filters else Song.objects.all()
    songs = songs[:100]

    nodes = []
    links = []
    node_id = 0
    node_map = {}

    for song in songs:
        song_id = f"song_{song.song_id}"
        if song_id not in node_map:
            symbol = ''
            if song.song_img:
                symbol = 'image://' + song.song_img.url
            elif song.song_img_url:
                symbol = 'image://' + song.song_img_url

            nodes.append({
                "id": song_id,
                "name": song.song_name,
                "category": 0,
                "symbolSize": 30,
                "symbol": symbol,
                "itemStyle": {
                    "opacity": 0.8
                }
            })
            node_map[song_id] = node_id
            node_id += 1

        singer_id = f"singer_{song.song_singer}"
        if singer_id not in node_map:
            nodes.append({
                "id": singer_id,
                "name": song.song_singer,
                "category": 1,
                "symbolSize": 25
            })
            node_map[singer_id] = node_id
            node_id += 1

        album_id = f"album_{song.song_album}"
        if album_id not in node_map:
            nodes.append({
                "id": album_id,
                "name": song.song_album,
                "category": 2,
                "symbolSize": 20
            })
            node_map[album_id] = node_id
            node_id += 1

        links.append({
            "source": node_map[song_id],
            "target": node_map[singer_id],
            "value": "演唱"
        })
        links.append({
            "source": node_map[song_id],
            "target": node_map[album_id],
            "value": "所属专辑"
        })

    for song in songs:
        song_id = f"song_{song.song_id}"

        lang_id = f"lang_{song.song_languages}"
        if lang_id not in node_map:
            nodes.append({
                "id": lang_id,
                "name": song.song_languages,
                "category": 3,
                "symbolSize": 15
            })
            node_map[lang_id] = node_id
            node_id += 1
            links.append({
                "source": node_map[song_id],
                "target": node_map[lang_id],
                "value": "语种"
            })

        if song.song_release:
            release_id = f"release_{song.song_release}"
            if release_id not in node_map:
                nodes.append({
                    "id": release_id,
                    "name": song.song_release,
                    "category": 4,
                    "symbolSize": 15
                })
                node_map[release_id] = node_id
                node_id += 1
                links.append({
                    "source": node_map[song_id],
                    "target": node_map[release_id],
                    "value": "发行时间"
                })

    categories = [
        {"name": "歌曲"},
        {"name": "歌手"},
        {"name": "专辑"},
        {"name": "语种"},
        {"name": "发行时间"}
    ]

    return JsonResponse({
        "nodes": nodes,
        "links": links,
        "categories": categories,
        "filtered": bool(filters)
    }, json_dumps_params={'ensure_ascii': False})