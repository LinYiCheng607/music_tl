import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from index.models import Song

class Command(BaseCommand):
    help = '从CSV文件中导入歌词到数据库中'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='CSV文件路径')
        parser.add_argument('--encoding', type=str, default='utf-8', help='CSV文件编码')
        parser.add_argument('--delimiter', type=str, default=',', help='CSV文件分隔符')
        parser.add_argument('--dry-run', action='store_true', help='仅检测不更新')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        encoding = options['encoding']
        delimiter = options['delimiter']
        dry_run = options['dry_run']

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'文件不存在: {csv_file}'))
            return

        self.stdout.write(self.style.NOTICE(f'开始从{csv_file}导入歌词...'))
        
        # 统计计数器
        total_songs = 0
        updated_songs = 0
        skipped_songs = 0
        not_found_songs = 0
        
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # 检查CSV文件是否包含必要的列
                required_columns = ['歌名', '歌手', '歌词']
                for column in required_columns:
                    if column not in reader.fieldnames:
                        self.stdout.write(self.style.ERROR(f'CSV文件缺少必要的列: {column}'))
                        return
                
                # 开始处理每一行
                for row in reader:
                    total_songs += 1
                    song_name = row['歌名'].strip()
                    song_singer = row['歌手'].strip()
                    lyrics = row['歌词']
                    
                    # 跳过空歌词
                    if not lyrics or lyrics.strip() == '':
                        skipped_songs += 1
                        continue
                    
                    # 查找匹配的歌曲
                    songs = Song.objects.filter(song_name=song_name, song_singer=song_singer)
                    
                    if not songs.exists():
                        not_found_songs += 1
                        self.stdout.write(self.style.WARNING(f'未找到歌曲: {song_name} - {song_singer}'))
                        continue
                    
                    # 更新歌词
                    if not dry_run:
                        with transaction.atomic():
                            for song in songs:
                                song.lyrics_text = lyrics
                                song.save()
                                updated_songs += 1
                                self.stdout.write(f'更新歌词: {song_name} - {song_singer}')
                    else:
                        updated_songs += songs.count()
                        self.stdout.write(f'将更新歌词: {song_name} - {song_singer}')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入过程中发生错误: {str(e)}'))
            return
        
        # 输出统计结果
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS(f'导入完成!'))
        self.stdout.write(self.style.SUCCESS(f'总歌曲数: {total_songs}'))
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'将更新歌词数: {updated_songs} (试运行模式)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已更新歌词数: {updated_songs}'))
        self.stdout.write(self.style.SUCCESS(f'跳过空歌词数: {skipped_songs}'))
        self.stdout.write(self.style.SUCCESS(f'未找到歌曲数: {not_found_songs}'))
        self.stdout.write(self.style.SUCCESS('='*50)) 