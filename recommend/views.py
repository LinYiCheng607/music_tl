from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from user.models import SongLog
from .models import ItemSimilarity, ArtistSimilarity
from index.models import Song
from comment.models import Comment
import numpy as np
from collections import defaultdict
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@login_required
def recommend_songs(request):
    """基于歌手的协同过滤推荐视图"""
    # 获取用户听歌记录中的歌手
    user_song_logs = SongLog.objects.filter(user=request.user).values('song').distinct()
    
    if not user_song_logs:
        # 默认热门歌曲推荐
        hot_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:10]
        nlp_recommendations = get_lyric_emotion_recommendations(user=request.user)
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': False,
            'nlp_recommendations': nlp_recommendations
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
        nlp_recommendations = get_lyric_emotion_recommendations(user=request.user)
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': True,
            'nlp_recommendations': nlp_recommendations
        })
    
    # 获取相似歌手的歌曲
    recommended_artist_names = [artist for artist, _ in sorted_artists[:5]]  # 取前5个相似歌手
    recommended_songs = Song.objects.filter(
        song_singer__in=recommended_artist_names
    ).exclude(
        song_id__in=song_ids
    ).order_by('-dynamic__dynamic_plays')[:10]
    
    nlp_recommendations = get_lyric_emotion_recommendations(user=request.user)
    # 获取推荐标题
    favorite_singers = get_favorite_singers(user=request.user)
    singer_title = f"您最爱听的歌手有：{', '.join(favorite_singers)}" if favorite_singers else "为您推荐相似歌手的歌曲"
    
    favorite_features = get_favorite_features(user=request.user)
    emotion_title = f"您最爱听的歌曲的特点都是：{', '.join(favorite_features)}" if favorite_features else "为您推荐相似情感的歌曲"
    
    return render(request, 'recommend/index.html', {
        'recommendations': recommended_songs,
        'has_history': True,
        'nlp_recommendations': nlp_recommendations,
        'singer_title': singer_title,
        'emotion_title': emotion_title
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


def get_favorite_singers(user, limit=3):
    """获取用户最爱听的歌手列表"""
    if not user.is_authenticated:
        return []
    singer_counts = SongLog.objects.filter(user=user).values('song__song_singer').annotate(play_count=Count('id')).order_by('-play_count')[:limit]
    return [item['song__song_singer'] for item in singer_counts]


def get_favorite_features(user, limit=3):
    """获取用户评论中最常出现的歌曲特点"""
    if not user.is_authenticated:
        return []
    # 假设Comment模型有tags字段关联到Tag模型，Tag模型有name字段
    tag_counts = Comment.objects.filter(comment_user=user).exclude(tags=None).values('tags__name').annotate(tag_count=Count('tags')).order_by('-tag_count')[:limit]
    return [item['tags__name'] for item in tag_counts]


def get_lyric_emotion_recommendations(user=None, top_n=10):
    """基于歌词情感分析的推荐"""
    # 1. 分析所有歌曲的歌词情感，生成情感标签
    song_emotions = {}
    songs = Song.objects.all()
    
    # 情感分析函数
    def analyze_emotion(text):
        if not text or text.strip() == '暂无歌词':
            return 'neutral'
        try:
            s = SnowNLP(text)
            sentiment = s.sentiments
            if sentiment > 0.6:
                return 'happy'
            elif sentiment < 0.4:
                return 'sad'
            else:
                return 'neutral'
        except:
            return 'neutral'
    
    # 使用预计算的情感标签
    for song in songs:
        song_emotions[song] = song.emotion_label or 'neutral'
    
    # 2. 获取用户评论中最常使用的标签
    user_top_tags = []
    if user:
        # 获取用户所有评论的标签
        user_tags = Comment.objects.filter(comment_user=user).values('tags__name').annotate(
            count=Count('tags__name')
        ).order_by('-count')
        
        # 提取前3个最常用标签
        user_top_tags = [tag['tags__name'] for tag in user_tags[:3]]
    
    # 3. 匹配策略：优先匹配情感标签与用户评论标签
    recommended_songs = []
    
    if user_top_tags:
        # 标签-情感映射关系
        tag_emotion_map = {
            '开心': 'happy',
            '伤感': 'sad',
            '兴奋': 'happy',
            '放松': 'neutral',
            '怀旧': 'neutral',
            '其他': 'neutral'
        }
        
        # 将用户标签转换为目标情感
        target_emotions = set()
        for tag in user_top_tags:
            target_emotions.add(tag_emotion_map.get(tag, 'neutral'))
        
        # 筛选具有目标情感标签的歌曲
        recommended_songs = [song for song, emotion in song_emotions.items() if emotion in target_emotions]
    else:
        # 若无用户标签，使用用户最常听的情感类型
        if user:
            user_heard_song_ids = SongLog.objects.filter(user=user).values_list('song_id', flat=True)
            heard_songs_emotions = [song_emotions[song] for song in song_emotions if song.song_id in user_heard_song_ids]
            
            if heard_songs_emotions:
                from collections import Counter
                most_common_emotion = Counter(heard_songs_emotions).most_common(1)[0][0]
                recommended_songs = [song for song, emotion in song_emotions.items() if emotion == most_common_emotion]
    
    # 4. 处理推荐结果
    if not recommended_songs:
        recommended_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:top_n*2]
    
    # 排除用户已听过的歌曲
    if user:
        user_heard_song_ids = SongLog.objects.filter(user=user).values_list('song_id', flat=True)
        recommended_songs = [song for song in recommended_songs if song.song_id not in user_heard_song_ids]
    
    # 返回Top N推荐
    return recommended_songs[:top_n]



