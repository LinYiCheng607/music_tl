from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from user.models import SongLog
from .models import ItemSimilarity, ArtistSimilarity
from index.models import Song
import numpy as np
from collections import defaultdict

@login_required
def recommend_songs(request):
    """基于歌手的协同过滤推荐视图"""
    # 获取用户听歌记录中的歌手
    user_song_logs = SongLog.objects.filter(user=request.user).values('song').distinct()
    if not user_song_logs:
        # 默认热门歌曲推荐
        hot_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:10]
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': False
        })
    
    # 提取用户听过的歌手
    song_ids = [log['song'] for log in user_song_logs]
    user_artists = set(Song.objects.filter(song_id__in=song_ids).values_list('song_singer', flat=True))
    if not user_artists:
        hot_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:10]
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': False
        })
    
    # 查找相似歌手
    similar_artists = defaultdict(float)
    for artist in user_artists:
        # 查询与当前歌手相似的其他歌手（双向匹配）
        similarities = ArtistSimilarity.objects.filter(
            Q(artist1=artist) | Q(artist2=artist)
        )
        for sim in similarities:
            similar_artist = sim.artist2 if sim.artist1 == artist else sim.artist1
            if similar_artist not in user_artists:
                similar_artists[similar_artist] += sim.similarity_score
    
    # 排序相似歌手
    sorted_artists = sorted(similar_artists.items(), key=lambda x: x[1], reverse=True)
    if not sorted_artists:
        hot_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:10]
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': True
        })
    
    # 获取相似歌手的歌曲
    recommended_artist_names = [artist for artist, _ in sorted_artists[:5]]  # 取前5个相似歌手
    recommended_songs = Song.objects.filter(
        song_singer__in=recommended_artist_names
    ).exclude(
        song_id__in=song_ids
    ).order_by('-dynamic__dynamic_plays')[:10]
    
    return render(request, 'recommend/index.html', {
        'recommendations': recommended_songs,
        'has_history': True
    })


def update_similarity_scores():
    """更新物品相似度分数的函数（可通过定时任务或管理命令调用）"""
    # 获取所有歌曲ID
    all_song_ids = list(Song.objects.values_list('song_id', flat=True))
    if not all_song_ids:
        return

    # 构建物品-用户矩阵（歌曲被哪些用户听过）
    song_user_matrix = defaultdict(set)
    for log in SongLog.objects.all():
        song_user_matrix[log.song_id].add(log.user_id)

    # 计算物品共现矩阵
    co_occurrence = defaultdict(lambda: defaultdict(int))
    for song1 in all_song_ids:
        for song2 in all_song_ids:
            if song1 == song2:
                continue
            # 计算共同听过的用户数
            users1 = song_user_matrix.get(song1, set())
            users2 = song_user_matrix.get(song2, set())
            co_occurrence[song1][song2] = len(users1 & users2)

    # 计算余弦相似度并保存
    for song1 in all_song_ids:
        for song2 in all_song_ids:
            if song1 == song2:
                continue
            # 获取听过两首歌曲的用户集合
            users1 = song_user_matrix.get(song1, set())
            users2 = song_user_matrix.get(song2, set())
            # 计算余弦相似度
            count_both = len(users1 & users2)
            count1 = len(users1)
            count2 = len(users2)

            if count1 > 0 and count2 > 0:
                similarity = count_both / np.sqrt(count1 * count2)
                if similarity > 0:
                    # 更新或创建相似度记录
                    ItemSimilarity.objects.update_or_create(
                        song1_id=song1,
                        song2_id=song2,
                        defaults={'similarity_score': similarity}
                    )

def update_artist_similarity_scores():
    """更新歌手相似度分数的函数"""
    # 获取所有用户的听歌记录，按用户分组
    user_artist_matrix = defaultdict(set)
    for log in SongLog.objects.all().select_related('song'):
        artist = log.song.song_singer
        user_artist_matrix[log.user_id].add(artist)
    
    # 计算歌手共现矩阵
    co_occurrence = defaultdict(lambda: defaultdict(int))
    for user_id, artists in user_artist_matrix.items():
        artist_list = list(artists)
        for i in range(len(artist_list)):
            for j in range(i+1, len(artist_list)):
                artist_a = artist_list[i]
                artist_b = artist_list[j]
                co_occurrence[artist_a][artist_b] += 1
                co_occurrence[artist_b][artist_a] += 1
    
    # 计算余弦相似度并保存
    all_artists = list(co_occurrence.keys())
    for artist1 in all_artists:
        for artist2 in all_artists:
            if artist1 == artist2:
                continue
            # 获取共同用户数
            count_both = co_occurrence[artist1].get(artist2, 0)
            count1 = sum(1 for users in user_artist_matrix.values() if artist1 in users)
            count2 = sum(1 for users in user_artist_matrix.values() if artist2 in users)
            
            if count1 > 0 and count2 > 0:
                similarity = count_both / np.sqrt(count1 * count2)
                if similarity > 0:
                    # 确保artist1按字母顺序在前，避免重复
                    if artist1 > artist2:
                        artist1, artist2 = artist2, artist1
                    ArtistSimilarity.objects.update_or_create(
                        artist1=artist1,
                        artist2=artist2,
                        defaults={'similarity_score': similarity}
                    )



