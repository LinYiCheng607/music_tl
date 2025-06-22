from django.shortcuts import render, redirect
from django.http import HttpResponse
from index.models import *
from django.http import StreamingHttpResponse
import os

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
    
    return render(request, 'play.html', locals())


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
    
    # 使用默认的歌曲文件路径
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           'static', 'songFile', 'default.mp3')
    
    # 如果歌曲文件存在，则使用实际文件
    if hasattr(song_info.song_file, 'name') and song_info.song_file.name:
        real_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                    'static', 'songFile', song_info.song_file.name)
        if os.path.exists(real_file_path):
            file_path = real_file_path

    def file_iterator(file_path, chunk_size=512):
        with open(file_path, 'rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break
    
    # 将文件内容写入StreamingHttpResponse对象，并以字节流的方式返回给用户，实现文件下载
    filename = str(song_id) + '.mp3'
    response = StreamingHttpResponse(file_iterator(file_path))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="%s"' % filename
    return response

