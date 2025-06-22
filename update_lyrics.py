import os
import csv
import django
import sys
import traceback

# 设置Django环境
print("开始设置Django环境...")
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "music.settings")
    django.setup()
    from index.models import Song
    print("Django环境设置成功")
except Exception as e:
    print(f"Django环境设置失败: {e}")
    traceback.print_exc()
    sys.exit(1)

def update_korean_songs_lyrics():
    try:
        # 获取所有韩文歌曲
        korean_songs = Song.objects.filter(song_languages="韩文")
        print(f"数据库中共有 {korean_songs.count()} 首韩文歌曲")
        
        # 统计缺少歌词的歌曲数量
        no_lyrics_count = korean_songs.filter(lyrics_text__isnull=True).count() + korean_songs.filter(lyrics_text="").count()
        print(f"其中 {no_lyrics_count} 首歌曲缺少歌词")
        
        # 读取CSV文件中的歌词信息
        csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "韩国songs.csv")
        print(f"尝试读取CSV文件: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            print(f"错误: CSV文件不存在: {csv_file_path}")
            return
        
        songs_data = {}
        
        try:
            # 尝试不同的编码方式
            encodings = ['utf-8', 'utf-8-sig', 'gb18030', 'gbk', 'gb2312']
            
            for encoding in encodings:
                try:
                    print(f"尝试使用 {encoding} 编码读取CSV文件...")
                    with open(csv_file_path, "r", encoding=encoding) as file:
                        # 读取第一行以确认列名
                        first_line = file.readline().strip()
                        print(f"CSV文件的第一行: {first_line}")
                        
                        # 解析第一行，查找列名
                        headers = first_line.split(',')
                        print(f"解析的列名: {headers}")
                        
                        # 确认列名索引
                        song_name_idx = -1
                        artist_idx = -1
                        lyrics_idx = -1
                        
                        for i, header in enumerate(headers):
                            header = header.strip()
                            if header == "歌名":
                                song_name_idx = i
                            elif header == "歌手":
                                artist_idx = i
                            elif header == "歌词":
                                lyrics_idx = i
                        
                        print(f"列索引 - 歌名: {song_name_idx}, 歌手: {artist_idx}, 歌词: {lyrics_idx}")
                        
                        if song_name_idx != -1 and artist_idx != -1 and lyrics_idx != -1:
                            print(f"成功使用 {encoding} 编码找到所有必要的列名")
                            break
                except UnicodeDecodeError:
                    print(f"{encoding} 编码读取失败")
                    continue
                        
            if song_name_idx == -1 or artist_idx == -1 or lyrics_idx == -1:
                print("CSV文件缺少必要的列名")
                return
                
            # 重新打开文件读取数据
            with open(csv_file_path, "r", encoding=encoding) as file:
                # 跳过标题行
                next(file)
                
                # 从CSV读取歌词数据
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    
                    row = line.split(',')
                    if len(row) > max(song_name_idx, artist_idx, lyrics_idx):
                        song_name = row[song_name_idx]
                        artist = row[artist_idx]
                        lyrics = row[lyrics_idx]
                        
                        key = (song_name, artist)
                        if lyrics and lyrics.strip():
                            songs_data[key] = lyrics
        except Exception as e:
            print(f"读取CSV文件时出错: {e}")
            traceback.print_exc()
            return
        
        print(f"CSV文件中共有 {len(songs_data)} 首带歌词的歌曲")
        
        # 如果没有歌曲数据，则退出
        if not songs_data:
            print("CSV文件中没有找到歌词数据")
            return
        
        # 更新数据库中缺少歌词的歌曲
        updated_count = 0
        for song in korean_songs:
            # 检查是否缺少歌词
            if not song.lyrics_text or song.lyrics_text.strip() == "":
                key = (song.song_name, song.song_singer)
                if key in songs_data:
                    song.lyrics_text = songs_data[key]
                    song.save()
                    updated_count += 1
                    print(f"已更新: {song.song_name} - {song.song_singer}")
        
        print(f"成功更新了 {updated_count} 首歌曲的歌词")
    except Exception as e:
        print(f"更新歌词时出错: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("开始更新韩文歌曲歌词...")
    update_korean_songs_lyrics()
    print("脚本执行完成")
