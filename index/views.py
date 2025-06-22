from django.shortcuts import render
from .models import *
import random
import os
from django.http import HttpResponse
from django.conf import settings
# Create your views here.


def indexview(request):
    # 热搜歌曲
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:12]
    # 音乐分类
    label_list = Label.objects.all()
    # 热门歌曲
    play_hot_song = Dynamic.objects.select_related('song').order_by('-dynamic_plays').all()[10:20]
    # 新歌推荐
    daily_recommendation = Song.objects.order_by('-song_release').all()[:3]
    # 热门搜索、热门下载
    search_ranking = search_song[:12]
    down_ranking = Dynamic.objects.select_related('song').order_by('-dynamic_down').all()[:12]
    all_ranking = [search_ranking, down_ranking]
    return render(request, 'index.html', locals())


def random_image(request):
    """随机返回一张已下载的图片"""
    # 图片目录路径
    img_dir = os.path.join(settings.STATICFILES_DIRS[0], 'songImg')
    
    # 获取所有图片文件
    img_files = [f for f in os.listdir(img_dir) if f.endswith('.jpg') and not f == 'default.jpg']
    
    if not img_files:
        # 如果没有图片，返回默认图片
        with open(os.path.join(img_dir, 'default.jpg'), 'rb') as f:
            return HttpResponse(f.read(), content_type="image/jpeg")
    
    # 随机选择一张图片
    random_img = random.choice(img_files)
    
    # 读取并返回图片内容
    with open(os.path.join(img_dir, random_img), 'rb') as f:
        return HttpResponse(f.read(), content_type="image/jpeg")


# 500
def page_error(request):
    return render(request, 'error404.html', status=500)

# 404
def page_not_found(request, exception):
    return render(request, 'error404.html', status=404)
