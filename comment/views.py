from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator
from index.models import Song, Dynamic
from django.db.models import Sum
from .models import Comment, Scene, Tag
from django.urls import reverse
import time
import json

# Create your views here.

# 预设标签和场景
def create_initial_tags_and_scenes():
    # 预设标签
    tags = [
        "旋律优美", "歌词走心", "唱功出色", "节奏感强", "编曲精彩", "朗朗上口",
    ]
    
    # 预设场景
    scenes = [
        "运动", "学习", "休闲", "派对", "通勤", "睡前",
    ]
    
    # 创建标签
    for tag_name in tags:
        Tag.objects.get_or_create(name=tag_name)
    
    # 创建场景
    for scene_name in scenes:
        Scene.objects.get_or_create(name=scene_name)


# 点评页面视图
def comment_view(request, songid):
    # 确保初始标签和场景存在
    create_initial_tags_and_scenes()
    
    # 热搜歌曲
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_down')[:7]
    # 获取当前歌曲
    song_info = Song.objects.filter(song_id=songid).first()
    
    # 歌曲不存在，抛出异常
    if not song_info:
        raise Http404("歌曲不存在")
    
    if request.method == 'POST':
        # 处理表单提交
        user_name = request.user.username if request.user.is_authenticated else '匿名用户'
        rating = request.POST.get('rating')
        emotion = request.POST.get('emotion')
        comment_text = request.POST.get('comment')
        selected_tags = request.POST.getlist('tags')
        selected_scenes = request.POST.getlist('scene')
        
        # 创建评论
        comment = Comment.objects.create(
            comment_user=user_name,
            song=song_info,
            rating=rating,
            emotion=emotion,
            comment_text=comment_text,
            comment_date=time.strftime('%Y-%m-%d', time.localtime(time.time()))
        )
        
        # 添加标签
        tag_mapping = {
            "melodic": "旋律优美",
            "lyrics": "歌词走心",
            "vocal": "唱功出色",
            "rhythm": "节奏感强",
            "arrangement": "编曲精彩",
            "catchy": "朗朗上口"
        }
        
        # 添加标签
        if selected_tags:
            for tag_value in selected_tags:
                tag_name = tag_mapping.get(tag_value, tag_value)
                tag, created = Tag.objects.get_or_create(name=tag_name)
                comment.tags.add(tag)
            
        # 场景映射
        scene_mapping = {
            "workout": "运动",
            "study": "学习",
            "relax": "休闲",
            "party": "派对",
            "commute": "通勤",
            "sleep": "睡前"
        }
        
        # 添加场景
        if selected_scenes:
            for scene_value in selected_scenes:
                scene_name = scene_mapping.get(scene_value, scene_value)
                scene, created = Scene.objects.get_or_create(name=scene_name)
                comment.scenes.add(scene)
        
        # 重定向到点评页面并添加成功参数
        return HttpResponseRedirect(f'{reverse("comment", args=[songid])}?comment_success=1')
    
    # 获取所有评论
    comment_all = Comment.objects.filter(song=song_info).order_by('-comment_date')
    # 设置分页
    paginator = Paginator(comment_all, 5)  # 每页5条评论
    page = request.GET.get('page', 1)
    contacts = paginator.get_page(page)
    
    return render(request, 'comment.html', {
        'song_id': songid,
        'song_name': song_info.song_name,
        'comment_all': comment_all,
        'contacts': contacts,
        'search_song': search_song,
    })


# 新的歌曲点评视图 - 提交后自动跳转回播放页面
def song_review_view(request, songid):
    # 确保初始标签和场景存在
    create_initial_tags_and_scenes()
    
    # 热搜歌曲
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_down')[:7]
    # 获取当前歌曲
    song_info = Song.objects.filter(song_id=songid).first()
    
    # 歌曲不存在，抛出异常
    if not song_info:
        raise Http404("歌曲不存在")
    
    # 获取返回URL（默认为歌曲播放页面）
    return_url = request.GET.get('return_url', reverse('play', args=[songid]))
    comment_success = False
    
    if request.method == 'POST':
        # 处理表单提交
        user_name = request.user.username if request.user.is_authenticated else '匿名用户'
        rating = request.POST.get('rating')
        emotion = request.POST.get('emotion')
        comment_text = request.POST.get('comment')
        selected_tags = request.POST.getlist('tags')
        selected_scenes = request.POST.getlist('scene')
        
        # 创建评论
        comment = Comment.objects.create(
            comment_user=user_name,
            song=song_info,
            rating=rating,
            emotion=emotion,
            comment_text=comment_text,
            comment_date=time.strftime('%Y-%m-%d', time.localtime(time.time()))
        )
        
        # 添加标签
        tag_mapping = {
            "melodic": "旋律优美",
            "lyrics": "歌词走心",
            "vocal": "唱功出色",
            "rhythm": "节奏感强",
            "arrangement": "编曲精彩",
            "catchy": "朗朗上口"
        }
        
        # 添加标签
        if selected_tags:
            for tag_value in selected_tags:
                tag_name = tag_mapping.get(tag_value, tag_value)
                tag, created = Tag.objects.get_or_create(name=tag_name)
                comment.tags.add(tag)
            
        # 场景映射
        scene_mapping = {
            "workout": "运动",
            "study": "学习",
            "relax": "休闲",
            "party": "派对",
            "commute": "通勤",
            "sleep": "睡前"
        }
        
        # 添加场景
        if selected_scenes:
            for scene_value in selected_scenes:
                scene_name = scene_mapping.get(scene_value, scene_value)
                scene, created = Scene.objects.get_or_create(name=scene_name)
                comment.scenes.add(scene)
        
        # 设置成功标志
        comment_success = True
        
        # 如果是Ajax请求，返回JSON响应
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(json.dumps({'success': True, 'redirect': return_url}), content_type='application/json')
        
    # 获取所有评论
    comment_all = Comment.objects.filter(song=song_info).order_by('-comment_date')
    # 设置分页
    paginator = Paginator(comment_all, 5)  # 每页5条评论
    page = request.GET.get('page', 1)
    contacts = paginator.get_page(page)
    
    return render(request, 'song_review.html', {
        'song_info': song_info,
        'song_id': songid,
        'comment_all': comment_all,
        'contacts': contacts,
        'search_song': search_song,
        'return_url': return_url,
        'comment_success': comment_success,
    })

