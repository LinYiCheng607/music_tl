from django.shortcuts import render
from index.models import *
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# Create your views here.


def rankingview(request):
    # 热搜歌曲
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:4]
    
    allowed_types = ['华语', '欧美', '日本', '韩国']
    All_list = Song.objects.filter(song_type__in=allowed_types).values('song_type').distinct()
    
    song_type = request.GET.get('type', '')
    page = request.GET.get('page', 1)
    page_size = 10

    if song_type in allowed_types:
        base_query = Dynamic.objects.select_related('song').filter(song__song_type=song_type).order_by('-dynamic_plays')
    else:
        song_type = '华语'
        base_query = Dynamic.objects.select_related('song').filter(song__song_type=song_type).order_by('-dynamic_plays')

    from django.core.paginator import Paginator
    
    # 使用Paginator实现分页查询，每页10条数据
    paginator = Paginator(base_query, page_size)
    try:
        song_info = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        song_info = paginator.page(1)

    return render(request, 'ranking.html', locals())
