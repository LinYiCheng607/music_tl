from django.shortcuts import render, redirect
from django.http import HttpResponse
from index.models import *
from django.http import StreamingHttpResponse
import os
import random

# Create your views here.


def playview(request, song_id):
    # 热搜歌曲
    search_song = Dynamic.objects.select_related('song').order_by('-dynamic_search').all()[:6]
    
    # 歌曲信息
    try:
        song_info = Song.objects.get(song_id=int(song_id))
    except Song.DoesNotExist:
        # 歌曲不存在，重定向到首页或显示错误信息
        error_message = f"抱歉，ID为{song_id}的歌曲不存在。"
        # 获取一些推荐歌曲，展示在错误页面中
        recommend_songs = Song.objects.all()[:10]
        return render(request, 'error.html', {
            'error_message': error_message,
            'recommend_songs': recommend_songs
        })
    
    # 获取所有可用的歌曲文件
    song_file_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'songFile')
    available_song_files = []
    if os.path.exists(song_file_dir):
        available_song_files = [f for f in os.listdir(song_file_dir) if os.path.isfile(os.path.join(song_file_dir, f)) and f.endswith(('.mp3', '.m4a', '.ogg'))]
    
    # 处理歌曲文件路径
    song_file_name = None
    # 首先尝试使用song_id匹配文件（如果有）
    song_id_files = [f for f in available_song_files if f.startswith(f"{song_id}.")]
    if song_id_files:
        song_file_name = song_id_files[0]
    else:
        # 然后尝试使用歌曲名称匹配文件（如果有）
        song_name_files = [f for f in available_song_files if song_info.song_name in f]
        if song_name_files:
            song_file_name = song_name_files[0]
        else:
            # 如果找不到匹配的文件，检查数据库中的song_file是否有效
            if hasattr(song_info.song_file, 'name') and song_info.song_file.name:
                song_file_name = song_info.song_file.name
                song_file_path = os.path.join(song_file_dir, song_file_name)
                if not os.path.exists(song_file_path):
                    # 如果数据库中的文件不存在，随机选择一个可用的文件
                    song_file_name = random.choice(available_song_files) if available_song_files else "爱你.m4a"
            else:
                # 随机选择一个可用的文件
                song_file_name = random.choice(available_song_files) if available_song_files else "爱你.m4a"
    
    # 播放列表
    play_list = request.session.get('play_list', [])
    song_exist = False
    if play_list:
        for i in play_list:
            if int(song_id) == i['song_id']:
                song_exist = True
    if not song_exist:
        play_list.append({'song_id': int(song_id), 'song_singer': song_info.song_singer,
                          'song_name': song_info.song_name, 'song_time': song_info.song_time})
        request.session['play_list'] = play_list
    
    # 歌词处理
    song_lyrics = "暂无歌词"  # 默认歌词
    
    # 优先使用lyrics_text字段中的歌词内容
    if song_info.lyrics_text:
        song_lyrics = song_info.lyrics_text
    # 如果lyrics_text为空，尝试读取歌词文件
    elif song_info.song_lyrics and song_info.song_lyrics != '暂无歌词':
        try:
            # 尝试读取歌词文件
            lyrics_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     'static', 'songLyric', 'default.txt')
            if hasattr(song_info.song_lyrics, 'name') and song_info.song_lyrics.name:
                if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          'static', 'songLyric', song_info.song_lyrics.name)):
                    lyrics_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          'static', 'songLyric', song_info.song_lyrics.name)
            
            with open(lyrics_path, 'r', encoding='utf-8') as f:
                song_lyrics = f.read()
        except (OSError, IOError):
            # 如果读取失败，设置为默认歌词
            song_lyrics = "暂无歌词"
    
    # 相关歌曲
    song_types = Song.objects.values('song_type').get(song_id=song_id)
    song_relevant = Dynamic.objects.select_related('song').filter(song__song_type=song_types.get('song_type')).order_by('dynamic_plays').all()[:6]
    
    # 添加播放次数
    dynamic_info = Dynamic.objects.filter(song_id=int(song_id)).first()
    if dynamic_info:
        dynamic_info.dynamic_plays += 1
        dynamic_info.save()
    else:
        dynamic_info = Dynamic(dynamic_plays=1, dynamic_search=0, dynamic_down=0, song_id=song_id)
        dynamic_info.save()
    
    return render(request, 'play.html', {'search_song': search_song, 'song_info': song_info, 
                                         'play_list': play_list, 'song_lyrics': song_lyrics, 
                                         'song_relevant': song_relevant, 'song_file_name': song_file_name})


def downloadview(request, song_id):
    # 根据song_id查找歌曲信息
    try:
        song_info = Song.objects.get(song_id=int(song_id))
    except Song.DoesNotExist:
        # 歌曲不存在
        return HttpResponse("抱歉，您请求下载的歌曲不存在。", status=404)
    
    # 添加下载次数
    dynamic_info = Dynamic.objects.filter(song_id=song_id).first()
    # 判断歌曲信息是否存在，存在就在原来基础上加
    if dynamic_info:
        dynamic_info.dynamic_down += 1
        dynamic_info.save()
    # 不存在
    else:
        dynamic_info = Dynamic(dynamic_plays=0, dynamic_search=0, dynamic_down=1, song_id=song_id)
        dynamic_info.save()
    
    # 获取所有可用的歌曲文件
    song_file_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'songFile')
    available_song_files = []
    if os.path.exists(song_file_dir):
        available_song_files = [f for f in os.listdir(song_file_dir) if os.path.isfile(os.path.join(song_file_dir, f)) and f.endswith(('.mp3', '.m4a', '.ogg'))]
    
    # 处理歌曲文件路径
    song_file_name = None
    file_path = None
    
    # 首先尝试使用song_id匹配文件（如果有）
    song_id_files = [f for f in available_song_files if f.startswith(f"{song_id}.")]
    if song_id_files:
        song_file_name = song_id_files[0]
        file_path = os.path.join(song_file_dir, song_file_name)
    else:
        # 然后尝试使用歌曲名称匹配文件（如果有）
        song_name_files = [f for f in available_song_files if song_info.song_name in f]
        if song_name_files:
            song_file_name = song_name_files[0]
            file_path = os.path.join(song_file_dir, song_file_name)
        else:
            # 如果找不到匹配的文件，检查数据库中的song_file是否有效
            if hasattr(song_info.song_file, 'name') and song_info.song_file.name:
                song_file_name = song_info.song_file.name
                file_path = os.path.join(song_file_dir, song_file_name)
                if not os.path.exists(file_path):
                    # 如果数据库中的文件不存在，随机选择一个可用的文件
                    song_file_name = random.choice(available_song_files) if available_song_files else "爱你.m4a"
                    file_path = os.path.join(song_file_dir, song_file_name)
            else:
                # 随机选择一个可用的文件
                song_file_name = random.choice(available_song_files) if available_song_files else "爱你.m4a"
                file_path = os.path.join(song_file_dir, song_file_name)

    def file_iterator(file_path, chunk_size=512):
        with open(file_path, 'rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    
    # 将文件内容写入StreamingHttpResponse对象，并以字节流的方式返回给用户，实现文件下载
    file_extension = song_file_name.split('.')[-1] if '.' in song_file_name else 'm4a'
    filename = f"{song_id}.{file_extension}"
    response = StreamingHttpResponse(file_iterator(file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="%s"' % filename
    return response

