from django.core.management.base import BaseCommand
from index.models import Song, Label, Dynamic
from django.db.models import Q

class Command(BaseCommand):
    help = '检查系统中所有的韩语歌曲'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('正在查找所有韩语歌曲...'))
        
        # 搜索语种为"韩"的歌曲
        korean_songs = Song.objects.filter(
            Q(song_languages__contains='韩')
        )
        
        count = korean_songs.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('数据库中没有韩语歌曲'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'找到 {count} 首韩语歌曲，开始显示详情...'))
        
        for song in korean_songs:
            self.stdout.write(self.style.SUCCESS(
                f'ID: {song.song_id} | '
                f'歌名: {song.song_name} | '
                f'歌手: {song.song_singer} | '
                f'语种: {song.song_languages} | '
                f'专辑: {song.song_album}'
            ))
        
        self.stdout.write(self.style.SUCCESS(f'共有 {count} 首韩语歌曲')) 