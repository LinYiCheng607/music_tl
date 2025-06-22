from django.core.management.base import BaseCommand
from index.models import Song
from django.db.models import Q

class Command(BaseCommand):
    help = '检查哪些歌曲有歌词，哪些歌曲没有歌词'

    def add_arguments(self, parser):
        parser.add_argument('--show-songs', action='store_true', help='显示具体的歌曲名称')
        parser.add_argument('--limit', type=int, default=10, help='显示的歌曲数量限制')

    def handle(self, *args, **options):
        show_songs = options['show_songs']
        limit = options['limit']
        
        # 查询有歌词的歌曲
        songs_with_lyrics = Song.objects.filter(
            Q(lyrics_text__isnull=False) & ~Q(lyrics_text='')
        )
        
        # 查询没有歌词的歌曲
        songs_without_lyrics = Song.objects.filter(
            Q(lyrics_text__isnull=True) | Q(lyrics_text='')
        )
        
        # 输出统计信息
        total_songs = Song.objects.count()
        with_lyrics_count = songs_with_lyrics.count()
        without_lyrics_count = songs_without_lyrics.count()
        
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'歌曲总数: {total_songs}'))
        self.stdout.write(self.style.SUCCESS(f'有歌词的歌曲数: {with_lyrics_count} ({with_lyrics_count/total_songs*100:.2f}%)'))
        self.stdout.write(self.style.SUCCESS(f'没有歌词的歌曲数: {without_lyrics_count} ({without_lyrics_count/total_songs*100:.2f}%)'))
        self.stdout.write(self.style.SUCCESS('='*50))
        
        # 如果需要显示具体歌曲
        if show_songs:
            if with_lyrics_count > 0:
                self.stdout.write(self.style.SUCCESS('\n有歌词的歌曲示例:'))
                for song in songs_with_lyrics[:limit]:
                    self.stdout.write(f'ID: {song.song_id}, 歌名: {song.song_name}, 歌手: {song.song_singer}')
                    
            if without_lyrics_count > 0:
                self.stdout.write(self.style.SUCCESS('\n没有歌词的歌曲示例:'))
                for song in songs_without_lyrics[:limit]:
                    self.stdout.write(f'ID: {song.song_id}, 歌名: {song.song_name}, 歌手: {song.song_singer}') 