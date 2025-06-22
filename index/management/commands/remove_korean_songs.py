from django.core.management.base import BaseCommand
from index.models import Song, Label, Dynamic
from django.db.models import Q

class Command(BaseCommand):
    help = '删除显示为问号的韩文歌曲'

    def handle(self, *args, **options):
        # 删除显示为问号的韩文歌曲
        self.stdout.write(self.style.SUCCESS('开始删除显示为问号的韩文歌曲...'))
        
        # 搜索歌名中包含"？"或歌手名中包含"？"且语种为"韩"的歌曲
        problematic_songs = Song.objects.filter(
            (Q(song_name__contains='？') | Q(song_singer__contains='？')) & 
            Q(song_languages__contains='韩')
        )
        
        if not problematic_songs:
            self.stdout.write(self.style.SUCCESS('没有找到问题韩文歌曲'))
            return
            
        count_deleted = problematic_songs.count()
        self.stdout.write(self.style.SUCCESS(f'找到 {count_deleted} 首问题韩文歌曲，正在删除...'))
        
        for song in problematic_songs:
            self.stdout.write(self.style.SUCCESS(f'删除歌曲: {song.song_id} - {song.song_name} - {song.song_singer}'))
            # 同时删除对应的动态记录
            Dynamic.objects.filter(song=song).delete()
            song.delete()
        
        self.stdout.write(self.style.SUCCESS(f'成功删除 {count_deleted} 首问题韩文歌曲')) 