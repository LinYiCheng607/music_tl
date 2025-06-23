#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查歌曲文件是否存在
"""

import os
import django
import sys

# 将项目根目录添加到Python路径中
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'music.settings')
django.setup()

# 导入模型
from index.models import Song

def check_song_files():
    """检查歌曲文件是否存在"""
    print("开始检查歌曲文件...")
    songs = Song.objects.all()
    total = songs.count()
    missing = 0
    
    for i, song in enumerate(songs):
        if not hasattr(song.song_file, 'name') or not song.song_file.name:
            print(f"[{i+1}/{total}] 警告: 歌曲 '{song.song_name}' (ID: {song.song_id}) 没有关联歌曲文件。")
            missing += 1
            continue
        
        file_path = os.path.join(BASE_DIR, 'static', 'songFile', song.song_file.name)
        if not os.path.exists(file_path):
            print(f"[{i+1}/{total}] 警告: 歌曲 '{song.song_name}' (ID: {song.song_id}) 的文件 '{song.song_file.name}' 不存在。")
            missing += 1
    
    print(f"\n检查完成: 总共 {total} 首歌曲，其中 {missing} 首歌曲文件缺失或不存在。")
    
    # 检查static/songFile目录中存在但数据库中未引用的文件
    song_dir = os.path.join(BASE_DIR, 'static', 'songFile')
    if os.path.exists(song_dir):
        all_files = set(os.listdir(song_dir))
        used_files = set(song.song_file.name for song in songs if hasattr(song.song_file, 'name') and song.song_file.name)
        unused_files = all_files - used_files
        
        if unused_files:
            print(f"\n发现 {len(unused_files)} 个未在数据库中引用的歌曲文件:")
            for file in sorted(unused_files):
                print(f"- {file}")

if __name__ == '__main__':
    check_song_files() 