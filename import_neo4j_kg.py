from py2neo import Graph, Node, Relationship
import os
import django

# 1. Django环境初始化
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "music.settings")  # 修改为你的项目名
django.setup()

from index.models import Song  # 你的Song表在index app下

# 2. 连接Neo4j
graph = Graph("bolt://localhost:7687", auth=("neo4j", "2111601205"))  # 修改密码

def merge_node(label, unique_key, props):
    node = Node(label, **props)
    graph.merge(node, label, unique_key)
    return node

def main():
    print("导入实体节点...")

    # 歌曲实体
    for song in Song.objects.all():
        merge_node("Song", "song_id", {
            "song_id": song.song_id,
            "name": song.song_name
        })

    # 唯一歌手、专辑、类型、语种实体
    singers = set(Song.objects.values_list('song_singer', flat=True))
    albums = set(Song.objects.values_list('song_album', flat=True))
    types = set(Song.objects.values_list('song_type', flat=True))
    languages = set(Song.objects.values_list('song_languages', flat=True))

    for singer in singers:
        if singer:
            merge_node("Singer", "name", {"name": singer})
    for album in albums:
        if album:
            merge_node("Album", "name", {"name": album})
    for t in types:
        if t:
            merge_node("Type", "name", {"name": t})
    for lang in languages:
        if lang:
            merge_node("Language", "name", {"name": lang})

    print("实体节点导入完成。")
    print("导入关系...")

    for song in Song.objects.all():
        song_node = graph.nodes.match("Song", song_id=song.song_id).first()
        if not song_node:
            continue

        # 歌曲-歌手
        if song.song_singer:
            singer_node = graph.nodes.match("Singer", name=song.song_singer).first()
            if singer_node:
                graph.merge(Relationship(song_node, "SUNG_BY", singer_node))

        # 歌曲-专辑
        if song.song_album:
            album_node = graph.nodes.match("Album", name=song.song_album).first()
            if album_node:
                graph.merge(Relationship(song_node, "IN_ALBUM", album_node))

        # 歌曲-类型
        if song.song_type:
            type_node = graph.nodes.match("Type", name=song.song_type).first()
            if type_node:
                graph.merge(Relationship(song_node, "BELONGS_TO", type_node))

        # 歌曲-语种
        if song.song_languages:
            lang_node = graph.nodes.match("Language", name=song.song_languages).first()
            if lang_node:
                graph.merge(Relationship(song_node, "IN_LANGUAGE", lang_node))

    print("知识图谱导入流程结束！")

if __name__ == "__main__":
    main()