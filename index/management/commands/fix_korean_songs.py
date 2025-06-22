import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from index.models import Song, Label, Dynamic
from django.db.models import Q

class Command(BaseCommand):
    help = '删除显示为问号的韩文歌曲并从CSV文件重新导入'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='韩文歌曲CSV文件的路径')
        parser.add_argument('--label', type=int, default=1, help='要导入的歌曲的标签ID，默认为1')
        parser.add_argument('--encoding', type=str, default='utf-8', help='CSV文件的编码，默认为utf-8')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        label_id = options['label']
        encoding = options['encoding']
        
        # 确保标签存在
        try:
            label = Label.objects.get(label_id=label_id)
        except Label.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'标签ID {label_id} 不存在，请先创建标签'))
            return
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在：{csv_file_path}'))
            return
        
        # 1. 删除显示为问号的韩文歌曲
        self.stdout.write(self.style.SUCCESS('开始删除显示为问号的韩文歌曲...'))
        # 搜索歌名中包含"？"或歌手名中包含"？"且语种为"韩语"的歌曲
        problematic_songs = Song.objects.filter(
            (Q(song_name__contains='？') | Q(song_singer__contains='？')) & 
            Q(song_languages__contains='韩')
        )
        
        count_deleted = problematic_songs.count()
        for song in problematic_songs:
            # 同时删除对应的动态记录
            Dynamic.objects.filter(song=song).delete()
            song.delete()
        
        self.stdout.write(self.style.SUCCESS(f'成功删除 {count_deleted} 首问题韩文歌曲'))
        
        # 2. 从CSV文件重新导入韩文歌曲
        self.stdout.write(self.style.SUCCESS('开始从CSV文件导入韩文歌曲...'))
        
        # 确保图片目录存在
        img_dir = os.path.join(settings.BASE_DIR, 'static', 'songImg')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        
        # 导入数据
        try:
            with open(csv_file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                songs_imported = 0
                
                for row in reader:
                    try:
                        song_name = row.get('歌名', '')
                        song_singer = row.get('歌手', '')
                        
                        # 如果歌名或歌手为空，则跳过
                        if not song_name or not song_singer:
                            self.stdout.write(self.style.WARNING('跳过缺少歌名或歌手的记录'))
                            continue
                        
                        # 设置默认图片路径
                        img_path = 'default.jpg'
                        
                        # 检查歌曲是否已存在
                        existing_song = Song.objects.filter(
                            Q(song_name=song_name) & Q(song_singer=song_singer)
                        ).first()
                        
                        if existing_song:
                            # 跳过已存在的歌曲
                            self.stdout.write(self.style.WARNING(f'跳过已存在的歌曲：{song_name} - {song_singer}'))
                            continue
                        
                        # 创建新歌曲记录
                        song = Song(
                            song_name=song_name,
                            song_singer=song_singer,
                            song_time=row.get('时长', ''),
                            song_album=row.get('专辑', ''),
                            song_languages='韩语',  # 确保设置为韩语
                            song_type=row.get('类型', ''),
                            song_release=row.get('发行时间', ''),
                            song_img=img_path,  # 使用默认图片
                            song_lyrics='default.txt',
                            song_file='default.mp3',
                            label=label
                        )
                        song.save()
                        
                        # 创建动态记录（初始播放、搜索、下载次数为0）
                        dynamic = Dynamic(
                            song=song,
                            dynamic_plays=0,
                            dynamic_search=0,
                            dynamic_down=0
                        )
                        dynamic.save()
                        
                        songs_imported += 1
                        
                        # 每导入100首歌曲显示一次进度
                        if songs_imported % 100 == 0:
                            self.stdout.write(self.style.SUCCESS(f'已导入 {songs_imported} 首歌曲'))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'导入歌曲 {row.get("歌名", "未知")} 时出错：{str(e)}'))
                
                self.stdout.write(self.style.SUCCESS(f'导入完成！成功导入 {songs_imported} 首韩文歌曲'))
        except UnicodeDecodeError:
            self.stdout.write(self.style.ERROR(f'无法使用 {encoding} 编码读取文件。请尝试其他编码，如 gbk, utf-8-sig, cp936 等'))
            return 