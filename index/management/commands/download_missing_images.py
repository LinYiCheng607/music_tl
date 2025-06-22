import os
import urllib.request
import time
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from index.models import Song

class Command(BaseCommand):
    help = '下载缺失的歌曲图片'

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=100, help='每批处理的歌曲数量，默认为100')
        parser.add_argument('--delay', type=float, default=0.2, help='每次下载之间的延迟时间（秒），默认为0.2秒')
        parser.add_argument('--force', action='store_true', help='强制重新下载所有图片')

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        delay = options['delay']
        force = options['force']
        
        # 默认图片URL列表
        default_image_urls = [
            'https://img1.baidu.com/it/u=3709586903,2067517058&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            'https://img0.baidu.com/it/u=2184091571,1981259050&fm=253&fmt=auto&app=120&f=JPEG?w=800&h=800',
            'https://img1.baidu.com/it/u=1817953371,2741172&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            'https://img1.baidu.com/it/u=736028137,1105825656&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            'https://img2.baidu.com/it/u=2946490913,1205325932&fm=253&fmt=auto&app=120&f=JPEG?w=1280&h=800',
            'https://img0.baidu.com/it/u=3271611136,2174609233&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            'https://img2.baidu.com/it/u=2313954513,4224895672&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            'https://img0.baidu.com/it/u=3224708146,2469524124&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500',
            'https://img2.baidu.com/it/u=1003272215,1878948666&fm=253&fmt=auto&app=120&f=JPEG?w=1280&h=800',
            'https://img1.baidu.com/it/u=2893416227,3920207331&fm=253&fmt=auto&app=138&f=JPEG?w=500&h=500'
        ]
        
        # 图片存储目录
        img_dir = os.path.join(settings.BASE_DIR, 'static', 'songImg')
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
            
        # 获取所有歌曲
        songs = Song.objects.all()
        total_songs = songs.count()
        self.stdout.write(self.style.SUCCESS(f'共找到 {total_songs} 首歌曲'))
        
        # 统计信息
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 批量处理歌曲
        for i in range(0, total_songs, batch_size):
            batch = songs[i:i+batch_size]
            self.stdout.write(self.style.SUCCESS(f'正在处理第 {i+1} 到 {min(i+batch_size, total_songs)} 首歌曲'))
            
            for song in batch:
                try:
                    # 检查图片文件是否已存在
                    img_path = str(song.song_img)
                    img_filename = os.path.basename(img_path)
                    local_img_path = os.path.join(img_dir, img_filename)
                    
                    if not force and os.path.exists(local_img_path) and os.path.getsize(local_img_path) > 1000:
                        skip_count += 1
                        continue
                    
                    # 构造图片文件名
                    new_img_filename = f"1_{song.song_singer}_{song.song_name}.jpg"
                    new_img_filename = new_img_filename.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                    
                    # 限制文件名长度，避免文件名过长
                    if len(new_img_filename) > 200:
                        new_img_filename = new_img_filename[:190] + '.jpg'
                        
                    new_local_img_path = os.path.join(img_dir, new_img_filename)
                    
                    # 随机选择一个默认图片URL
                    default_image_url = random.choice(default_image_urls)
                    
                    # 尝试下载图片
                    try:
                        urllib.request.urlretrieve(default_image_url, new_local_img_path)
                        
                        # 更新数据库中的图片路径
                        song.song_img = new_img_filename
                        song.save()
                        
                        success_count += 1
                        if success_count % 10 == 0:
                            self.stdout.write(self.style.SUCCESS(f'已成功下载 {success_count} 张图片'))
                    except Exception as e:
                        fail_count += 1
                        self.stdout.write(self.style.ERROR(f'下载图片失败：{song.song_name} - {song.song_singer}, 错误: {str(e)}'))
                    
                    # 添加延迟，避免请求过于频繁
                    time.sleep(delay + random.uniform(0, 0.2))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'处理歌曲时出错：{song.song_name} - {song.song_singer}, 错误: {str(e)}'))
            
            # 显示批次进度
            self.stdout.write(self.style.SUCCESS(f'已处理 {min(i+batch_size, total_songs)}/{total_songs} 首歌曲'))
        
        # 显示最终统计信息
        self.stdout.write(self.style.SUCCESS(f'处理完成！成功: {success_count}, 失败: {fail_count}, 跳过: {skip_count}')) 