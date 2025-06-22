import csv
import os
import urllib.request
from django.core.management.base import BaseCommand
from django.conf import settings
from index.models import Song, Label, Dynamic
from django.db.models import Q

class Command(BaseCommand):
    help = '从CSV文件导入歌曲数据到数据库'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='CSV文件的路径')
        parser.add_argument('--label', type=int, default=1, help='要导入的歌曲的标签ID，默认为1')
        parser.add_argument('--encoding', type=str, default='gb18030', help='CSV文件的编码，默认为gb18030')
        parser.add_argument('--overwrite', action='store_true', help='覆盖现有歌曲数据')
        parser.add_argument('--use-url', action='store_true', help='使用原始URL而不下载图片')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        label_id = options['label']
        encoding = options['encoding']
        overwrite = options['overwrite']
        use_url = options['use_url']
        
        # 确保标签存在
        try:
            label = Label.objects.get(label_id=label_id)
        except Label.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'标签ID {label_id} 不存在，请先创建标签'))
            return
        
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在：{csv_file_path}'))
            return
        
        # 确保图片目录存在
        img_dir = os.path.join(settings.BASE_DIR, 'static', 'songImg')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        
        # 导入数据
        try:
            with open(csv_file_path, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                songs_imported = 0
                songs_updated = 0
                
                for row in reader:
                    try:
                        song_name = row.get('歌名', '')
                        song_singer = row.get('歌手', '')
                        
                        # 处理图片链接
                        img_url = row.get('歌曲图片', '')
                        img_path = 'default.jpg'  # 默认图片路径
                        
                        if img_url and img_url.startswith('http'):
                            if use_url:
                                # 直接使用URL，不下载图片
                                img_path = 'default.jpg'  # 仍然设置一个默认本地图片路径
                            else:
                                # 从图片链接中提取文件名
                                img_filename = f"1_{song_singer}_{song_name}.jpg"
                                img_filename = img_filename.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                                local_img_path = os.path.join(img_dir, img_filename)
                                
                                try:
                                    # 尝试下载图片
                                    urllib.request.urlretrieve(img_url, local_img_path)
                                    img_path = img_filename
                                    self.stdout.write(self.style.SUCCESS(f'下载图片成功：{img_url}'))
                                except Exception as e:
                                    self.stdout.write(self.style.WARNING(f'下载图片失败：{img_url}, 错误: {str(e)}'))
                        
                        # 检查歌曲是否已存在
                        existing_song = Song.objects.filter(
                            Q(song_name=song_name) & Q(song_singer=song_singer)
                        ).first()
                        
                        if existing_song and overwrite:
                            # 更新现有记录
                            existing_song.song_time = row.get('时长', '')
                            existing_song.song_album = row.get('专辑', '')
                            existing_song.song_languages = row.get('语种', '')
                            existing_song.song_type = row.get('类型', '')
                            existing_song.song_release = row.get('发行时间', '')
                            existing_song.song_img = img_path
                            existing_song.song_img_url = img_url if use_url else ''  # 保存原始URL
                            existing_song.save()
                            
                            songs_updated += 1
                            self.stdout.write(self.style.SUCCESS(f'更新歌曲：{song_name} - {song_singer}'))
                        elif not existing_song:
                            # 创建新歌曲记录
                            song = Song(
                                song_name=song_name,
                                song_singer=song_singer,
                                song_time=row.get('时长', ''),
                                song_album=row.get('专辑', ''),
                                song_languages=row.get('语种', ''),
                                song_type=row.get('类型', ''),
                                song_release=row.get('发行时间', ''),
                                song_img=img_path,  # 使用下载的图片或默认图片
                                song_img_url=img_url if use_url else '',  # 保存原始URL
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
                        else:
                            # 歌曲存在但没有指定覆盖
                            self.stdout.write(self.style.WARNING(f'跳过已存在的歌曲：{song_name} - {song_singer}'))
                        
                        # 每导入/更新100首歌曲显示一次进度
                        total_processed = songs_imported + songs_updated
                        if total_processed % 100 == 0 and total_processed > 0:
                            self.stdout.write(self.style.SUCCESS(f'已处理 {total_processed} 首歌曲（新增: {songs_imported}, 更新: {songs_updated}）'))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'导入歌曲 {row.get("歌名", "未知")} 时出错：{str(e)}'))
                
                self.stdout.write(self.style.SUCCESS(f'导入完成！新增 {songs_imported} 首歌曲，更新 {songs_updated} 首歌曲'))
        except UnicodeDecodeError:
            self.stdout.write(self.style.ERROR(f'无法使用 {encoding} 编码读取文件。请尝试其他编码，如 gbk, utf-8-sig, cp936 等'))
            return 