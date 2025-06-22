import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = '创建歌曲媒体文件所需的目录结构'

    def handle(self, *args, **options):
        # 定义需要创建的目录
        media_root = os.path.join(settings.BASE_DIR, 'static/upload')
        dirs_to_create = [
            os.path.join(media_root, 'songImg'),
            os.path.join(media_root, 'songFile'),
            os.path.join(media_root, 'songLyric')
        ]
        
        for dir_path in dirs_to_create:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.stdout.write(self.style.SUCCESS(f'已创建目录：{dir_path}'))
            else:
                self.stdout.write(self.style.WARNING(f'目录已存在：{dir_path}'))
        
        # 添加默认文件
        default_files = [
            (os.path.join(media_root, 'songImg/default.jpg'), '# 默认歌曲图片'),
            (os.path.join(media_root, 'songFile/default.mp3'), '# 默认歌曲文件'),
            (os.path.join(media_root, 'songLyric/default.txt'), '暂无歌词')
        ]
        
        for file_path, content in default_files:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.stdout.write(self.style.SUCCESS(f'已创建默认文件：{file_path}'))
            else:
                self.stdout.write(self.style.WARNING(f'默认文件已存在：{file_path}'))
        
        self.stdout.write(self.style.SUCCESS('所有目录和默认文件创建完成！')) 