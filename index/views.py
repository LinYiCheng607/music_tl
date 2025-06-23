from django.core.paginator import Paginator
from django.shortcuts import render
from .models import *
import random
import os
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

# Create your views here.

def indexview(request):
    # 热搜歌曲 - 只显示有图片URL的歌曲
    search_song = Dynamic.objects.select_related('song').filter(
        ~Q(song__song_img_url='') & ~Q(song__song_img_url=None)
    ).order_by('-dynamic_search').all()[:12]
    
    # 音乐分类
    label_list = Label.objects.all()
    
    # 热门歌曲 - 只显示有图片URL的歌曲
    play_hot_song = Dynamic.objects.select_related('song').filter(
        ~Q(song__song_img_url='') & ~Q(song__song_img_url=None)
    ).order_by('-dynamic_plays').all()[:20]
    play_hot_song = play_hot_song[0:min(10, len(play_hot_song))]
    
    # 新歌推荐 - 只显示有图片URL的歌曲
    daily_recommendation = Song.objects.filter(
        ~Q(song_img_url='') & ~Q(song_img_url=None)
    ).order_by('-song_release').all()[:3]
    
    # 热门搜索、热门下载 - 只显示有图片URL的歌曲
    search_ranking = search_song[:12]
    down_ranking = Dynamic.objects.select_related('song').filter(
        ~Q(song__song_img_url='') & ~Q(song__song_img_url=None)
    ).order_by('-dynamic_down').all()[:12]
    
    # 分页逻辑
    # 热门搜索分页
    paginator_search = Paginator(search_ranking, 8)  # 每页显示12个
    page_number_search = request.GET.get('page')
    hot_search_pages = paginator_search.get_page(page_number_search)
    
    # 热门下载分页
    paginator_down = Paginator(down_ranking, 8)
    page_number_down = request.GET.get('page2')
    hot_download_pages = paginator_down.get_page(page_number_down)
    
    # 将分页对象传递给模板
    return render(request, 'index.html', {
        'search_song': search_song,
        'label_list': label_list,
        'play_hot_song': play_hot_song,
        'daily_recommendation': daily_recommendation,
        'hot_search_pages': hot_search_pages,
        'hot_download_pages': hot_download_pages,
    })

def random_image(request):
    """随机返回一张已下载的图片"""
    img_dir = os.path.join(settings.STATICFILES_DIRS[0], 'songImg')
    img_files = [f for f in os.listdir(img_dir) if f.endswith('.jpg') and not f == 'default.jpg']
    
    if not img_files:
        with open(os.path.join(img_dir, 'default.jpg'), 'rb') as f:
            return HttpResponse(f.read(), content_type="image/jpeg")
    
    random_img = random.choice(img_files)
    with open(os.path.join(img_dir, random_img), 'rb') as f:
        return HttpResponse(f.read(), content_type="image/jpeg")

# 500
def page_error(request):
    return render(request, 'error404.html', status=500)

# 404
def page_not_found(request, exception):
    return render(request, 'error404.html', status=404)