import os
import django
import sys

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "music.settings")
django.setup()

from index.models import Song

def check_korean_songs_lyrics():
    # 获取所有韩文歌曲
    korean_songs = Song.objects.filter(song_languages="韩文")
    print(f"数据库中共有 {korean_songs.count()} 首韩文歌曲")
    
    # 统计缺少歌词的歌曲数量
    no_lyrics_count = korean_songs.filter(lyrics_text__isnull=True).count() + korean_songs.filter(lyrics_text="").count()
    print(f"其中 {no_lyrics_count} 首歌曲仍缺少歌词")
    
    # 列出前10首缺少歌词的歌曲
    if no_lyrics_count > 0:
        print("\n仍缺少歌词的前10首歌曲:")
        missing_lyrics_songs = list(korean_songs.filter(lyrics_text__isnull=True)) + list(korean_songs.filter(lyrics_text=""))
        for i, song in enumerate(missing_lyrics_songs[:10]):
            print(f"{i+1}. {song.song_name} - {song.song_singer}")

if __name__ == "__main__":
    check_korean_songs_lyrics()
