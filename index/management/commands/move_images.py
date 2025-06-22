import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from index.models import Song

class Command(BaseCommand):
    help = '将图片从static/upload/songImg目录移动到static/songImg目录'

    def handle(self, *args, **options):
        # 源目录和目标目录
        source_dir = os.path.join(settings.BASE_DIR, 'static', 'upload', 'songImg')
        target_dir = os.path.join(settings.BASE_DIR, 'static', 'songImg')
        
        # 确保目标目录存在
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # 如果源目录不存在，显示错误并退出
        if not os.path.exists(source_dir):
            self.stdout.write(self.style.ERROR(f'源目录不存在：{source_dir}'))
            return
        
        # 遍历源目录中的所有文件
        files_moved = 0
        for filename in os.listdir(source_dir):
            source_path = os.path.join(source_dir, filename)
            target_path = os.path.join(target_dir, filename)
            
            # 只处理文件，不处理子目录
            if os.path.isfile(source_path):
                try:
                    # 如果目标文件已存在，先删除
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    
                    # 复制文件
                    shutil.copy2(source_path, target_path)
                    files_moved += 1
                    
                    if files_moved % 100 == 0:
                        self.stdout.write(self.style.SUCCESS(f'已移动 {files_moved} 个文件'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'移动文件 {filename} 时出错：{str(e)}'))
        
        # 更新数据库中的图片路径
        self.stdout.write(self.style.SUCCESS(f'移动完成！共移动 {files_moved} 个文件'))
        self.stdout.write(self.style.SUCCESS('正在更新数据库中的图片路径...'))
        
        updated_count = 0
        for song in Song.objects.all():
            if song.song_img:
                img_path = str(song.song_img)
                if img_path.startswith('songImg/'):
                    # 从路径中提取文件名
                    filename = os.path.basename(img_path)
                    song.song_img = filename
                    song.save()
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        self.stdout.write(self.style.SUCCESS(f'已更新 {updated_count} 条记录'))
        
        self.stdout.write(self.style.SUCCESS(f'数据库更新完成！共更新 {updated_count} 条记录')) 