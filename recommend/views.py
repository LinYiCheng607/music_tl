from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from user.models import SongLog
from .models import ItemSimilarity, ArtistSimilarity
from index.models import Dynamic, Song
from comment.models import Comment
from collections import Counter
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import implicit
from scipy.sparse import csr_matrix
import joblib
import os
from datetime import datetime
from django.db.models import Count, Max
from scipy.sparse import dok_matrix
from django.conf import settings
from implicit.als import AlternatingLeastSquares
import logging
logger = logging.getLogger(__name__)

@login_required
def recommend_songs(request):
    """获取推荐歌曲视图"""
    # 获取用户听歌记录中的歌手
    user_song_logs = SongLog.objects.filter(user=request.user).values('song').distinct()
    
    if not user_song_logs:
        # 默认热门歌曲推荐
        hot_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:10]
        # nlp_recommendations = asl_emotion_recommendations(user=request.user)
        title = "快来试下以下的热门歌曲吧~"
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': False,
            'singer_title' : title,
            'als_title': title,
            'emotion_title' : title
        })
    
    # 提取用户听过的歌手
    song_ids = [log['song'] for log in user_song_logs]
    user_artists = set(Song.objects.filter(song_id__in=song_ids).values_list('song_singer', flat=True))
    user_artists = set(artist for artist in user_artists if artist)
    if not user_artists:
        hot_songs = Song.objects.all().order_by('-dynamic__dynamic_plays')[:10]
        return render(request, 'recommend/index.html', {
            'recommendations': hot_songs,
            'has_history': False
        })
    # print(f'用户的听过的歌手：{user_artists}')
    # 查找相似歌手
    artists_from_user = []
    similar_artists = defaultdict(float)
    for artist in user_artists:
        # 查询与当前歌手相似的其他歌手（双向匹配）
        similarities = ArtistSimilarity.objects.filter(
            Q(artist1=artist) | Q(artist2=artist)
        )
        if artist not in artists_from_user:
            artists_from_user.append(artist)
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
    recommended_artist_names = [artist for artist, _ in sorted_artists[:5] if artist]  # 取前5个相似歌手
    # print(recommended_artist_names)
    recommended_songs = Song.objects.filter(
        song_singer__in=recommended_artist_names
    ).exclude(
        song_id__in=song_ids
    ).order_by('-dynamic__dynamic_plays')[:10]
    
    # 获取基于内容推荐的结果
    nlp_recommendations = asl_emotion_recommendations(user=request.user)
    # 获取ALS推荐结果
    als_recommendations_result = als_recommendations(user=request.user)
    # 获取推荐标题
    favorite_singers = get_favorite_singers(user=request.user)
    singer_title = f"与 {','.join(artists_from_user[:3])} 等的歌手类型相似的歌手有： {', '.join(recommended_artist_names[:3]) } 等" if favorite_singers else "为您推荐相似歌手的歌曲"

    
    favorite_features = get_favorite_features(user=request.user)
    emotion_title = f"您最近认为您听过的歌曲的情感为：{', '.join(favorite_features)}" if favorite_features else "还未为歌曲评论，快去评论吧~"
    
    return render(request, 'recommend/index.html', {
        'recommendations': recommended_songs,
        'has_history': True,
        'nlp_recommendations': nlp_recommendations,
        'als_recommendations': als_recommendations_result,
        'singer_title': singer_title,
        'emotion_title': emotion_title,
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
            # 获取听过的两首歌曲的用户集合
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


def build_user_item_matrix():
    from datetime import datetime
    from user.models import SongLog
    
    play_logs = SongLog.objects.values('user_id', 'song_id')\
        .annotate(
            play_count=Count('id'),
            last_played=Max('listen_time')
        )

    user_ids = {u['user_id']: i for i, u in enumerate(play_logs.values('user_id').distinct())}
    song_ids = {s['song_id']: j for j, s in enumerate(play_logs.values('song_id').distinct())}

    max_date = datetime.now().date()
    interactions = {}
    for log in play_logs:
        days_old = (max_date - log['last_played'].date()).days
        decay = 0.9 ** (days_old // 7)
        
        user_idx = user_ids[log['user_id']]
        song_idx = song_ids[log['song_id']]
        interactions[(user_idx, song_idx)] = log['play_count'] * decay

    matrix = dok_matrix((len(user_ids), len(song_ids)), dtype=np.float32)
    for (u, s), weight in interactions.items():
        matrix[u, s] = weight

    user_id_map = {uid: idx for idx, uid in enumerate(user_ids)}
    song_id_map = {sid: idx for idx, sid in enumerate(song_ids)}
    return matrix, user_id_map, song_id_map, user_ids, song_ids

def train_als_model():
    model_path = os.path.join(settings.BASE_DIR, 'recommend/models/als_model.pkl')
    
    try:
        # 加载模型时恢复完整元数据
        data = joblib.load(model_path)
        model = data['model']
        train_song_ids = data['song_ids']
        train_song_count = data['song_count']
        
        # 检查歌曲库变动
        current_song_count = Song.objects.count()
        if abs(current_song_count - train_song_count)/train_song_count > 0.05:
            logger.info(f"歌曲库变动超过5%({train_song_count}→{current_song_count})，触发重新训练")
            model = None
    
    except (FileNotFoundError, KeyError):
        model = None

    if not model:
        # 重新训练时生成完整元数据
        # 重新训练时生成完整元数据
        matrix, user_id_map, song_id_map, user_ids, song_ids = build_user_item_matrix()
        model = AlternatingLeastSquares(factors=100, regularization=0.01, iterations=20, random_state=42)
        model.fit(matrix)
        
        # 保存完整训练快照
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump({
            'model': model,
            'song_ids': song_ids,
            'song_id_map': song_id_map,
            'user_id_map': user_id_map,  # 新增用户映射保存
            'song_count': len(song_ids),
            'train_time': datetime.now()
        }, model_path)

    return model


def als_recommendations(user, top_n=10):
    model = train_als_model()
    
    # 加载训练时保存的元数据
    model_path = os.path.join(settings.BASE_DIR, 'recommend/models/als_model.pkl')
    data = joblib.load(model_path)
    train_song_ids = data['song_ids']
    # print(train_song_ids)
    song_id_map = data['song_id_map']
    user_id_map = data['user_id_map']  # 新增用户ID映射加载

    # 使用训练时的song_id_map转换索引
    user_interactions = SongLog.objects.filter(user=user).values('song_id').annotate(count=Count('song_id'))
    valid_song_ids = [log['song_id'] for log in user_interactions if log['song_id'] in song_id_map]

    # 构建用户向量（基于训练时的映射）
    from scipy.sparse import csr_matrix
    song_indices = [song_id_map[sid] for sid in valid_song_ids]
    interaction_counts = [log['count'] for log in user_interactions if log['song_id'] in song_id_map]
    
    try:
        user_vector = csr_matrix(
            (interaction_counts, ([0]*len(song_indices), song_indices)),
            shape=(1, len(train_song_ids))
        )
        logger.debug(f'用户向量构建成功，非零元素数量：{user_vector.nnz}')
    except Exception as e:
        logger.error(f'用户向量构建失败：{str(e)}')
        return Song.objects.none()

    # 获取推荐时使用训练时的song_ids验证
    max_index = len(train_song_ids) - 1
    user_idx = user_id_map[user.id]
    # 获取推荐结果
    recommendations = model.recommend(
        userid=user_idx,
        user_items=user_vector,
        N=top_n*2,
        filter_already_liked_items=True
    )
    # print(recommendations)
    
    # 解构推荐结果元组
    recommended_indices, scores = recommendations
    
    # 转换推荐索引为Python列表
    recommended_indices = recommended_indices.tolist()
    
    # 将推荐索引转换为歌曲ID
    # recommended_song_ids = train_song_ids[recommended_indices]
    recommended_song_ids = []
    for idx in recommended_indices:
        for key, value in train_song_ids.items():
            if value == idx:
                recommended_song_ids.append(key)
                break

    
    # 批量查询歌曲对象并保持推荐顺序
    recommended_songs = Song.objects.filter(song_id__in=recommended_song_ids)
    song_id_to_obj = {song.song_id: song for song in recommended_songs}
    # 保持推荐顺序
    ordered_songs = [song_id_to_obj[sid] for sid in recommended_song_ids if sid in song_id_to_obj]
    
    # 添加异常处理
    if not ordered_songs:
        logger.warning('No valid songs found for recommendations')
        return []
    
    return ordered_songs[:top_n]


def get_favorite_features(user, limit=3):
    """获取用户评论中最常出现的歌曲特点"""
    if not user.is_authenticated:
        return []
    
    EMOTION_CHOICES = {
        'happy': '开心',
        'sad': '伤感',
        'excited': '兴奋',
        'relaxed': '放松',
        'nostalgic': '怀旧',
        'other': '其他'
    }

    comment_emotions = Comment.objects.filter(comment_user=user).values('emotion').annotate(count=Count('emotion'))[:limit]
    comment_emotions = [EMOTION_CHOICES[item['emotion']] for item in comment_emotions]
    return comment_emotions



def build_emotion_feature_matrix():
    """构建用户情感特征矩阵和歌曲情感特征矩阵"""
    # 定义所有可能的情感标签（合并评论和歌曲的情感类型）
    EMOTION_LABELS = ['happy', 'sad', 'excited', 'relaxed', 'nostalgic']
    
    # 1. 构建用户情感特征矩阵 (用户ID -> 情感向量)
    user_emotions = defaultdict(dict)
    # 获取所有用户评论的情感数据
    comment_emotions = Comment.objects.values('comment_user', 'emotion').annotate(count=Count('emotion'))
    for item in comment_emotions:
        username = item['comment_user']
        emotion = item['emotion']
        count = item['count']
        if emotion not in user_emotions[username]:
            user_emotions[username][emotion] = 0
        user_emotions[username][emotion] += count
    # print(f'用户评论的情感数据：\n{user_emotions}')
    # 转换为标准化向量
    user_matrix = {}
    for username, emotions in user_emotions.items():
        total = sum(emotions.values())
        vector = [emotions.get(emotion, 0)/total for emotion in EMOTION_LABELS]
        user_matrix[username] = np.array(vector)
    # print(f'用户的标准化向量：\n{user_matrix}')
    # 2. 构建歌曲情感特征矩阵 (歌曲ID -> 情感向量)
    song_matrix = {}
    songs = Song.objects.all()
    for song in songs:
        # 初始化独热向量
        vector = np.zeros(len(EMOTION_LABELS))
        emotion = song.emotion_label
        # 映射歌曲情感标签到向量
        if emotion in EMOTION_LABELS:
            idx = EMOTION_LABELS.index(emotion)
            vector[idx] = 1
        song_matrix[song.song_id] = vector
    
    return user_matrix, song_matrix, EMOTION_LABELS


def asl_emotion_recommendations(user=None, top_n=10):
    """基于情感特征矩阵推荐"""
    if not user or not user.is_authenticated:
        # 未登录用户返回热门歌曲
        return Song.objects.all().order_by('-dynamic__dynamic_plays')[:top_n]
    
    # 获取情感特征矩阵
    user_matrix, song_matrix, emotion_labels = build_emotion_feature_matrix()
    username = user.username
    
    # 如果用户没有情感数据，使用基于听歌历史的情感推荐
    if username not in user_matrix:
        return get_history_based_emotion_recommendations(user, top_n)
    
    # 用户情感向量
    user_vector = user_matrix[username]
    
    # 计算用户与所有歌曲的余弦相似度
    similarities = {}
    for song_id, song_vector in song_matrix.items():
        # 避免除以零
        if np.linalg.norm(user_vector) == 0 or np.linalg.norm(song_vector) == 0:
            similarities[song_id] = 0
        else:
            similarities[song_id] = cosine_similarity([user_vector], [song_vector])[0][0]
    
    # 按相似度排序
    sorted_song_ids = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    # print(sorted_song_ids)
    # 排除已听过的歌曲
    heard_song_ids = set(SongLog.objects.filter(user=user).values_list('song_id', flat=True))
    recommended_song_ids = [sid for sid, _ in sorted_song_ids if sid not in heard_song_ids][:top_n*2]
    
    # 获取推荐歌曲并按相似度排序
    recommended_songs = Song.objects.filter(song_id__in=recommended_song_ids)
    
    # 按相似度重新排序查询结果
    song_id_to_song = {song.song_id: song for song in recommended_songs}
    recommended_songs = [song_id_to_song[sid] for sid in recommended_song_ids if sid in song_id_to_song][:top_n]

    # 如果推荐结果不足，用热门歌曲补充
    if len(recommended_songs) < top_n:
        hot_songs = Song.objects.filter(
            ~Q(song_id__in=heard_song_ids) & ~Q(song_id__in=recommended_song_ids)
        ).order_by('-dynamic__dynamic_plays')[:top_n - len(recommended_songs)]
        recommended_songs.extend(hot_songs)
    
    return recommended_songs[:top_n]


def get_history_based_emotion_recommendations(user, top_n=10):
    """基于用户听歌历史的情感推荐（回退策略）"""
    user_heard_song_ids = SongLog.objects.filter(user=user).values_list('song_id', flat=True)
    heard_songs = Song.objects.filter(song_id__in=user_heard_song_ids)
    
    # 统计听完歌曲的情感分布
    emotion_counter = Counter()
    for song in heard_songs:
        if song.emotion_label:
            emotion_counter[song.emotion_label] += 1
    
    if not emotion_counter:
        return Song.objects.all().order_by('-dynamic__dynamic_plays')[:top_n]
    
    # 选择最常听的情感类型
    most_common_emotion = emotion_counter.most_common(1)[0][0]
    
    # 推荐相同情感的歌曲
    recommended_songs = Song.objects.filter(
        emotion_label=most_common_emotion
    ).exclude(
        song_id__in=user_heard_song_ids
    ).order_by('-dynamic__dynamic_plays')[:top_n*2]
    
    return recommended_songs[:top_n]
    
    # 检查推荐结果是否为空
    if not recommended_song_ids:
        logger.warning('No valid recommendations found')