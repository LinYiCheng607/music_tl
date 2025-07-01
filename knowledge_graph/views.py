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
    graph = Graph("bolt://localhost:7687", auth=("neo4j", "2111601205"))

    if kg_type == 'artist-song':
        singers = graph.run("MATCH (si:Singer) RETURN si ORDER BY si.name").data()  # 不加LIMIT
        relations = ["SUNG_BY"]
        return JsonResponse({
            "nodes": [{"id": str(s["si"].identity), "name": s["si"]["name"]} for s in singers],
            "relations": relations
        })
    elif kg_type == 'song-album':
        albums = graph.run("MATCH (al:Album) RETURN al ORDER BY al.name").data()  # 不加LIMIT
        relations = ["IN_ALBUM"]
        return JsonResponse({
            "nodes": [{"id": str(a["al"].identity), "name": a["al"]["name"]} for a in albums],
            "relations": relations
        })
    elif kg_type == 'song-language':
        languages = graph.run("MATCH (l:Language) RETURN l ORDER BY l.name").data()  # 不加LIMIT
        relations = ["IN_LANGUAGE"]
        return JsonResponse({
            "nodes": [{"id": str(l["l"].identity), "name": l["l"]["name"]} for l in languages],
            "relations": relations
        })
    elif kg_type == 'song-type':
        types = graph.run("MATCH (t:Type) RETURN t ORDER BY t.name").data()  # 不加LIMIT
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
            # 查询该专辑的所有歌曲及IN_ALBUM关系
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
            # 查询该语言的所有歌曲及IN_LANGUAGE关系
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

    # 去重
    seen = set()
    unique_nodes = []
    for n in nodes:
        if n['id'] not in seen:
            seen.add(n['id'])
            unique_nodes.append(n)
    nodes = unique_nodes

    # 限制节点数量（只在展示图像时限制）
    if len(nodes) > LIMIT:
        nodes = nodes[:LIMIT]
        node_ids = set(n['id'] for n in nodes)
        # 只保留与这些节点相关的边
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
            model="moonshot-v1-8k",  # 免费额度支持的模型
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        reply = completion.choices[0].message.content
        print("moonshot content:", reply)
        # 容错：去除 markdown 代码块（兼容各种写法）
        reply = reply.strip()
        match = re.search(r"\{.*\}", reply, re.DOTALL)
        if match:
            reply = match.group()
        info = json.loads(reply)
        return info
    except Exception as e:
        print("解析moonshot失败：", e)
        return None

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

        # 1. 某歌手有哪些歌曲
        if intent and "歌手" in intent and "歌曲" in intent and singer:
            songs = Song.objects.filter(song_singer__icontains=singer)
            if not songs.exists():
                return JsonResponse({'error': f'未找到歌手：{singer}'}, status=404)
            nodes = [{
                'id': f'singer_{singer}',
                'name': singer,
                'labels': ['Singer'],
                'desc': f'歌手：{singer}'
            }]
            edges = []
            for song_obj in songs:
                nodes.append({
                    'id': f'song_{song_obj.song_id}',
                    'name': song_obj.song_name,
                    'labels': ['Song'],
                    'desc': f'歌曲：{song_obj.song_name}'
                })
                edges.append({
                    'source': f'singer_{singer}',
                    'target': f'song_{song_obj.song_id}',
                    'label': '演唱',
                    'desc': f'{singer}演唱'
                })
            desc = f"{singer}共收录{len(songs)}首歌曲：" + "、".join([s.song_name for s in songs[:10]]) + ("..." if len(songs) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 2. 某歌曲属于哪个专辑
        if intent and ("歌曲" in intent and "专辑" in intent) and song:
            try:
                song_obj = Song.objects.get(song_name__icontains=song)
            except Song.DoesNotExist:
                return JsonResponse({'error': f'未找到歌曲：{song}'}, status=404)
            album_name = song_obj.song_album
            nodes = [
                {'id': f'song_{song_obj.song_id}', 'name': song_obj.song_name, 'labels': ['Song'], 'desc': f'歌曲：{song_obj.song_name}'}
            ]
            edges = []
            if album_name:
                nodes.append({'id': f'album_{album_name}', 'name': album_name, 'labels': ['Album'], 'desc': f'专辑：{album_name}'})
                edges.append({'source': f'song_{song_obj.song_id}', 'target': f'album_{album_name}', 'label': '所属专辑', 'desc': f'属于专辑'})
                desc = f"《{song_obj.song_name}》属于专辑《{album_name}》"
            else:
                desc = f"未找到《{song_obj.song_name}》的专辑信息"
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 3. 某专辑有哪些歌曲
        if intent and ("专辑" in intent and "歌曲" in intent) and album:
            songs = Song.objects.filter(song_album__icontains=album)
            if not songs.exists():
                return JsonResponse({'error': f'未找到专辑：{album}'}, status=404)
            nodes = [{
                'id': f'album_{album}',
                'name': album,
                'labels': ['Album'],
                'desc': f'专辑：{album}'
            }]
            edges = []
            for song_obj in songs:
                nodes.append({
                    'id': f'song_{song_obj.song_id}',
                    'name': song_obj.song_name,
                    'labels': ['Song'],
                    'desc': f'歌曲：{song_obj.song_name}'
                })
                edges.append({
                    'source': f'album_{album}',
                    'target': f'song_{song_obj.song_id}',
                    'label': '收录',
                    'desc': f'专辑收录'
                })
            desc = f"专辑《{album}》收录{len(songs)}首歌曲：" + "、".join([s.song_name for s in songs[:10]]) + ("..." if len(songs) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 4. 某歌曲的语种
        if intent and ("歌曲" in intent and "语种" in intent) and song:
            try:
                song_obj = Song.objects.get(song_name__icontains=song)
            except Song.DoesNotExist:
                return JsonResponse({'error': f'未找到歌曲：{song}'}, status=404)
            lang = song_obj.song_languages or "未知"
            nodes = [
                {'id': f'song_{song_obj.song_id}', 'name': song_obj.song_name, 'labels': ['Song'], 'desc': f'歌曲：{song_obj.song_name}'},
                {'id': f'lang_{lang}', 'name': lang, 'labels': ['Language'], 'desc': f'语种：{lang}'}
            ]
            edges = [{'source': f'song_{song_obj.song_id}', 'target': f'lang_{lang}', 'label': '语种', 'desc': '语种'}]
            desc = f"《{song_obj.song_name}》的语种为：{lang}"
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        # 5. 某类型有哪些歌曲
        if intent and ("类型" in intent and "歌曲" in intent) and song_type:
            songs = Song.objects.filter(song_type__icontains=song_type)
            if not songs.exists():
                return JsonResponse({'error': f'未找到类型：{song_type}'}, status=404)
            nodes = [{
                'id': f'type_{song_type}',
                'name': song_type,
                'labels': ['Type'],
                'desc': f'类型：{song_type}'
            }]
            edges = []
            for song_obj in songs:
                nodes.append({
                    'id': f'song_{song_obj.song_id}',
                    'name': song_obj.song_name,
                    'labels': ['Song'],
                    'desc': f'歌曲：{song_obj.song_name}'
                })
                edges.append({
                    'source': f'type_{song_type}',
                    'target': f'song_{song_obj.song_id}',
                    'label': '属于类型',
                    'desc': f'属于类型'
                })
            desc = f"{song_type}类型共收录{len(songs)}首歌曲：" + "、".join([s.song_name for s in songs[:10]]) + ("..." if len(songs) > 10 else "")
            return JsonResponse({'nodes': nodes, 'edges': edges, 'description': desc})

        return JsonResponse({'error': '暂不支持此类问题'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'解析失败: {e}'}, status=500)
    
# search_knowledge_graph/views.py

def knowledge_graph(request):
    return render(request, 'search_knowledge_graph/graph.html')


def get_graph_data(request):
    # 获取筛选参数
    song_name = request.GET.get('song_name', '')
    singer = request.GET.get('singer', '')
    album = request.GET.get('album', '')
    language = request.GET.get('language', '')
    release = request.GET.get('release', '')

    # 构建查询条件
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

    # 应用筛选条件
    songs = Song.objects.filter(**filters) if filters else Song.objects.all()

    # 只取前300条数据
    songs = songs[:100]

    nodes = []
    links = []
    node_id = 0
    node_map = {}

    # 添加歌曲节点
    for song in songs:
        song_id = f"song_{song.song_id}"
        if song_id not in node_map:
            # 添加图片URL支持
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
                "symbol": symbol,  # 图片URL
                "itemStyle": {
                    "opacity": 0.8
                }
            })
            node_map[song_id] = node_id
            node_id += 1

        # 添加歌手节点
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

        # 添加专辑节点
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

        # 创建关系链接
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

    # 添加其他属性节点
    for song in songs:
        song_id = f"song_{song.song_id}"

        # 语言节点
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

        # 发行时间节点
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

    # 返回JSON响应
    return JsonResponse({
        "nodes": nodes,
        "links": links,
        "categories": categories,
        "filtered": bool(filters)  # 标记是否应用了筛选
    }, json_dumps_params={'ensure_ascii': False})