from django.shortcuts import render, redirect
from user.models import *
from django.db.models import Q
from django.contrib.auth import logout, login
from django.contrib.auth.hashers import check_password
from .form import MyUserCreationForm
from index.models import *
import json
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, Min
from django.http import JsonResponse
from collections import Counter
import pytz
from django.db.models.functions import TruncDate

def loginview(request):
    user = MyUserCreationForm()
    if request.method == 'POST':
        if request.POST.get('loginUser', ''):
            loginUser = request.POST.get('loginUser', '')
            password = request.POST.get('password', '')
            if MyUser.objects.filter(Q(mobile=loginUser) | Q(username=loginUser)):
                user = MyUser.objects.filter(Q(mobile=loginUser) | Q(username=loginUser)).first()
                if check_password(password, user.password):
                    login(request, user)
                    return redirect('/user/home/1.html')
                else:
                    tips = '密码错误'
            else:
                tips = '用户不存在'
        else:
            user = MyUserCreationForm(request.POST)
            if user.is_valid():
                user.save()
                tips = '注册成功'
            else:
                if user.errors.get('username'):
                    tips = user.errors.get('username', '注册失败1')
                else:
                    tips = user.errors.get('mobile', '注册失败2')
    return render(request, 'login.html', locals())

def logoutview(request):
    logout(request)
    return redirect('/')

@login_required(login_url='/user/login.html')
def homeview(request, page):
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:6]
    song_count_qs = (
        SongLog.objects
        .filter(user=request.user)
        .values(
            'song',
            'song__song_id',
            'song__song_name',
            'song__song_singer',
            'song__song_time',  
            'song__song_languages',
            'song__song_type'
        )
        .annotate(listen_count=Sum('listen_count'))
        .order_by('-listen_count', '-song')
    )
    song_info = [
        {
            'song_id': item['song__song_id'],
            'song_name': item['song__song_name'],
            'song_singer': item['song__song_singer'],
            'song_time': item['song__song_time'],
            'song_languages': item['song__song_languages'],
            'song_type': item.get('song__song_type', ''),
            'listen_count': item['listen_count'] or 0,
        }
        for item in song_count_qs
    ]
    paginator = Paginator(song_info, 10)
    try:
        contacts = paginator.page(page)
    except PageNotAnInteger:
        contacts = paginator.page(1)
    except EmptyPage:
        contacts = paginator.page(paginator.num_pages)
    return render(request, 'home.html', {
        'contacts': contacts,
        'search_song': search_song,
    })

@login_required
def song_analysis(request):
    user = request.user

    # 热门搜索
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:6]

    # 最近7天每天听歌数量
    today = timezone.now().date()
    days = 7
    line_labels = []
    line_data = []
    for i in range(days):
        day = today - timedelta(days=days - i - 1)
        line_labels.append(day.strftime('%Y-%m-%d'))
        cnt = SongLog.objects.filter(user=user, listen_time__date=day).count()
        line_data.append(cnt)

    # 不同类型的听歌次数
    pie_qs = (
        SongLog.objects
        .filter(user=user)
        .values('song__song_type')
        .annotate(value=Sum('listen_count'))
        .order_by('-value')
    )
    pie_data = []
    for item in pie_qs:
        pie_data.append({
            'name': item['song__song_type'] or '未知',
            'value': item['value']
        })

    # 每天听歌时段分布
    logs = SongLog.objects.filter(user=user)
    tz = pytz.timezone('Asia/Shanghai')
    hour_counts = [0] * 12
    hour_labels = [f"{2*i}-{2*i+2}点" for i in range(12)]
    for log in logs:
        local_time = log.listen_time.astimezone(tz)
        h = local_time.hour
        index = h // 2
        hour_counts[index] += 1

    # 近4周活跃度
    now = timezone.now()
    weekly_labels = []
    weekly_counts = []
    for i in range(4):
        start = now - timedelta(days=(i+1)*7)
        end = now - timedelta(days=i*7)
        count = logs.filter(listen_time__gte=start, listen_time__lt=end).count()
        weekly_labels.insert(0, f'第{4-i}周')
        weekly_counts.insert(0, count)

    # 最常听的歌手TOP5
    artist_counter = Counter()
    for log in logs.select_related("song"):
        artist = getattr(log.song, "song_singer", None)
        if artist:
            artist_counter[artist] += 1
    top_artists = artist_counter.most_common(5)
    artist_labels = [a[0] for a in top_artists]
    artist_data = [a[1] for a in top_artists]

    # 最常听的专辑TOP5
    album_counter = Counter()
    for log in logs.select_related("song"):
        album = getattr(log.song, "song_album", None)
        if album:
            album_counter[album] += 1
    top_albums = album_counter.most_common(5)
    album_labels = [a[0] for a in top_albums]
    album_data = [a[1] for a in top_albums]

    # 词云数据
    logs = SongLog.objects.filter(user=user).select_related("song")
    type_counter = Counter()
    artist_counter = Counter()
    album_counter = Counter()
    name_counter = Counter()
    for log in logs:
        if hasattr(log.song, "song_type") and log.song.song_type:
            type_counter[log.song.song_type] += 1
        if hasattr(log.song, "song_singer") and log.song.song_singer:
            artist_counter[log.song.song_singer] += 1
        if hasattr(log.song, "song_album") and log.song.song_album:
            album_counter[log.song.song_album] += 1
        if hasattr(log.song, "song_name") and log.song.song_name:
            name_counter[log.song.song_name] += 1

    wordcloud_type = [{"name": k, "value": v} for k, v in type_counter.items()]
    wordcloud_artist = [{"name": k, "value": v} for k, v in artist_counter.items()]
    wordcloud_album = [{"name": k, "value": v} for k, v in album_counter.items()]
    wordcloud_name = [{"name": k, "value": v} for k, v in name_counter.items()]

    # 听歌总榜TOP10（用于柱状图）
    top_songs = (
        SongLog.objects
        .filter(user=user)
        .values('song__song_name', 'song__song_singer', 'song__song_album', 'song__song_type')
        .annotate(listen_count=Sum('listen_count'))
        .order_by('-listen_count')[:10]
    )
    # 提取歌曲名和播放次数用于柱状图
    top_song_labels = [f"{item['song__song_name']}" for item in top_songs]
    top_song_counts = [item['listen_count'] for item in top_songs]

    # 月度听歌趋势（过去12个月）
    month_labels = []
    month_counts = []
    for i in range(12):
        month = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_str = month.strftime('%Y-%m')
        next_month = (month + timedelta(days=32)).replace(day=1)
        count = SongLog.objects.filter(user=user, listen_time__gte=month, listen_time__lt=next_month).count()
        month_labels.insert(0, month_str)
        month_counts.insert(0, count)

    # 听歌活跃日（听歌次数最多的日Top5）
    top_active_days = (
        SongLog.objects
        .filter(user=user)
        .annotate(date=TruncDate('listen_time'))
        .values('date')
        .annotate(count=Sum('listen_count'))
        .order_by('-count')[:5]
    )

    # 最常听的语种TOP5
    top_langs = (
        SongLog.objects
        .filter(user=user)
        .values('song__song_languages')
        .annotate(count=Sum('listen_count'))
        .order_by('-count')[:5]
    )
    top_langs = [{'language': item['song__song_languages'] or '未知', 'count': item['count']} for item in top_langs]

    # 听歌习惯总结
    fav_hour = hour_labels[hour_counts.index(max(hour_counts))] if any(hour_counts) else ""
    fav_artist = artist_labels[0] if artist_labels else ""
    trend = ("上升" if weekly_counts and weekly_counts[-1] > weekly_counts[0] else "下降") if weekly_counts else ""
    summary_text = f"你最常在{fav_hour}听歌，最近四周你的听歌频率有所{trend}，最常听的歌手是{fav_artist}……"

    context = {
        'line_labels': json.dumps(line_labels, ensure_ascii=False),
        'line_data': json.dumps(line_data, ensure_ascii=False),
        'pie_data': json.dumps(pie_data, ensure_ascii=False),
        'hourly_labels': json.dumps(hour_labels, ensure_ascii=False),
        'hourly_data': json.dumps(hour_counts),
        'weekly_labels': json.dumps(weekly_labels, ensure_ascii=False),
        'weekly_data': json.dumps(weekly_counts),
        'artist_labels': json.dumps(artist_labels, ensure_ascii=False),
        'artist_data': json.dumps(artist_data),
        'album_labels': json.dumps(album_labels, ensure_ascii=False),
        'album_data': json.dumps(album_data),
        'wordcloud_type': json.dumps(wordcloud_type, ensure_ascii=False),
        'wordcloud_artist': json.dumps(wordcloud_artist, ensure_ascii=False),
        'wordcloud_album': json.dumps(wordcloud_album, ensure_ascii=False),
        'wordcloud_name': json.dumps(wordcloud_name, ensure_ascii=False),
        'summary_text': summary_text,
        'search_song': search_song,
        'top_songs': top_songs,  # 如模板需要表格显示可保留
        'top_song_labels': json.dumps(top_song_labels, ensure_ascii=False),
        'top_song_counts': json.dumps(top_song_counts),
        'month_labels': json.dumps(month_labels, ensure_ascii=False),
        'month_counts': json.dumps(month_counts),
        'top_active_days': top_active_days,
        'top_langs': top_langs,
    }
    return render(request, 'song_analysis.html', context)

@login_required
def update_user_info(request):
    if request.method == "POST":
        user = request.user
        user.nickname = request.POST.get("nickname", user.nickname)
        user.email = request.POST.get("email", user.email)
        user.qq = request.POST.get("qq", user.qq)
        user.mobile = request.POST.get("mobile", user.mobile)
        user.bio = request.POST.get("bio", user.bio)
        user.save()
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "nickname": user.nickname,
                "email": user.email,
                "qq": user.qq,
                "mobile": user.mobile,
                "bio": user.bio,
            })
        return redirect("home", 1)
    return redirect("home", 1)