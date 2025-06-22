from django.shortcuts import render
from index.models import *
# Create your views here.


def rankingview(request):
    # 热搜歌曲
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:4]
    
    # 只保留华语、欧美、日本、韩国这四个排行榜
    allowed_types = ['华语', '欧美', '日本', '韩国']
    All_list = Song.objects.filter(song_type__in=allowed_types).values('song_type').distinct()
    
    # 歌曲列表信息
    song_type = request.GET.get('type', '')
    if song_type and song_type in allowed_types:
        song_info = Dynamic.objects.select_related('song').filter(song__song_type=song_type).order_by('-dynamic_plays').all()[:10]
    else:
        # 默认显示华语排行榜
        default_type = '华语'
        song_info = Dynamic.objects.select_related('song').filter(song__song_type=default_type).order_by('-dynamic_plays').all()[:10]
        song_type = default_type
    
    return render(request, 'ranking.html', locals())
