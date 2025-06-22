import csv
import os
from django.core.management.base import BaseCommand
from django.db.models import Q
from index.models import Song

class Command(BaseCommand):
    help = '从CSV文件更新歌曲图片URL'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='CSV文件的路径')
        parser.add_argument('--encoding', type=str, default='gb18030', help='CSV文件的编码，默认为gb18030')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        encoding = options['encoding']
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在：{csv_file_path}'))
            return
        
        # 导入数据
        try:
            with open(csv_file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                songs_updated = 0
                
                for row in reader:
                    try:
                        song_name = row.get('歌名', '')
                        song_singer = row.get('歌手', '')
                        img_url = row.get('歌曲图片', '')
                        
                        if not img_url or not img_url.startswith('http'):
                            continue
                        
                        # 查找匹配的歌曲
                        songs = Song.objects.filter(
                            Q(song_name=song_name) & Q(song_singer=song_singer)
                        )
                        
                        if songs.exists():
                            for song in songs:
                                song.song_img_url = img_url
                                song.save()
                                songs_updated += 1
                            
                            self.stdout.write(self.style.SUCCESS(f'更新歌曲图片URL：{song_name} - {song_singer} -> {img_url}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'未找到歌曲：{song_name} - {song_singer}'))
                        
                        # 每更新100首歌曲显示一次进度
                        if songs_updated % 100 == 0 and songs_updated > 0:
                            self.stdout.write(self.style.SUCCESS(f'已更新 {songs_updated} 首歌曲的图片URL'))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'更新歌曲 {row.get("歌名", "未知")} 的图片URL时出错：{str(e)}'))
                
                self.stdout.write(self.style.SUCCESS(f'更新完成！共更新 {songs_updated} 首歌曲的图片URL'))
        except UnicodeDecodeError:
            self.stdout.write(self.style.ERROR(f'无法使用 {encoding} 编码读取文件。请尝试其他编码，如 gbk, utf-8-sig, cp936 等'))
            return 