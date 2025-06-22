import csv
import re
from django.core.management.base import BaseCommand
from index.models import Song, Dynamic
from django.db.models import Q

class Command(BaseCommand):
    help = '识别、删除并重新导入有编码问题的韩文歌曲'

    def add_arguments(self, parser):
        parser.add_argument('--csv_file', type=str, help='韩文歌曲CSV文件的路径')
        parser.add_argument('--encoding', type=str, default='utf-8', help='CSV文件的编码，默认为utf-8')
        parser.add_argument('--only_show', action='store_true', help='仅显示问题歌曲，不执行删除操作')
        parser.add_argument('--force', action='store_true', help='强制删除所有匹配的问题歌曲，无需确认')

    def handle(self, *args, **options):
        csv_file_path = options.get('csv_file')
        encoding = options.get('encoding', 'utf-8')
        only_show = options.get('only_show', False)
        force = options.get('force', False)
        
        # 查找所有韩文歌曲
        self.stdout.write(self.style.SUCCESS('开始查找韩文歌曲...'))
        korean_songs = Song.objects.filter(Q(song_languages__contains='韩'))
        self.stdout.write(self.style.SUCCESS(f'共找到 {korean_songs.count()} 首韩文歌曲'))
        
        # 编码问题的识别标准
        problematic_songs = []
        for song in korean_songs:
            # 1. 专辑名称中包含问号是明确的编码问题
            album_has_question = '?' in song.song_album or '？' in song.song_album
            
            # 2. 歌名以问号开头或全是问号
            name_starts_with_question = song.song_name.startswith('?') or song.song_name.startswith('？')
            name_is_questions = song.song_name.strip('?').strip('？') == ''
            
            # 3. 歌手名中有问号
            singer_has_question = '?' in song.song_singer or '？' in song.song_singer
            
            # 4. 歌名有成对的问号表示是韩文字符(除正常情况)
            has_paired_questions = re.search(r'\?\S+\?', song.song_name)
            
            # 5. 专辑名中的"???"模式通常是韩文字符编码问题
            album_likely_korean = re.search(r'\?{2,}', song.song_album)
            
            # 正常的问号使用
            normal_patterns = [
                r"What is Love\?",
                r"Why So Serious\?",
                r"Am I\?",
                r"Who You\?",
                r"U&ME\?",
                r"YES or YES",
                r"CRY FOR ME",
                r"SAY MY NAME",
                r"STAND BY ME",
                r"LIKEY", 
                r"CHEER UP",
                r"FANCY",
                r"TT",
                r"I NEED A GIRL",
                r"FAMILY",
                r"STAY",
                r"FOREVER",
                r"DREAM",
                r"PROMISE"
            ]
            
            # 已知的正常歌曲ID，这些歌曲虽然含有问号，但实际上是正常的
            normal_song_ids = [
                2119805150,  # Why So Serious?
                2119799225,  # What is Love?
                2119799255,  # What is Love? -Japanese ver.-
            ]
            
            # 直接跳过已知正常的歌曲
            if song.song_id in normal_song_ids:
                continue
            
            is_normal = any(re.search(pattern, song.song_name, re.IGNORECASE) 
                           for pattern in normal_patterns)
            
            # 判断条件：专辑名有问号，或歌名以问号开头，或歌名是一堆问号，或歌名有成对问号且不是正常使用
            if (album_has_question or album_likely_korean or 
                (name_starts_with_question and not is_normal) or 
                name_is_questions or 
                (has_paired_questions and not is_normal) or
                (singer_has_question and song.song_name.count('?') > 1)):
                problematic_songs.append(song)
        
        self.stdout.write(self.style.SUCCESS(f'共找到 {len(problematic_songs)} 首存在编码问题的韩文歌曲'))
        
        # 显示有问题的歌曲
        for i, song in enumerate(problematic_songs, 1):
            self.stdout.write(self.style.SUCCESS(
                f'{i}. ID: {song.song_id} | '
                f'歌名: {song.song_name} | '
                f'歌手: {song.song_singer} | '
                f'语种: {song.song_languages} | '
                f'专辑: {song.song_album}'
            ))
        
        if only_show:
            self.stdout.write(self.style.SUCCESS('仅显示模式，不执行删除操作'))
            return
        
        # 删除有问题的歌曲
        if problematic_songs:
            confirmed = force
            if not force:
                confirm = input('是否删除以上有问题的歌曲？(y/n): ')
                confirmed = confirm.lower() == 'y'
                
            if confirmed:
                for song in problematic_songs:
                    try:
                        # 删除关联的动态记录
                        Dynamic.objects.filter(song=song).delete()
                        song.delete()
                        self.stdout.write(self.style.SUCCESS(f'已删除 ID: {song.song_id} - {song.song_name}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'删除歌曲 ID: {song.song_id} 时出错: {str(e)}'))
                
                self.stdout.write(self.style.SUCCESS(f'成功删除 {len(problematic_songs)} 首问题韩文歌曲'))
            else:
                self.stdout.write(self.style.SUCCESS('已取消删除操作'))
        
        # 如果提供了CSV文件，则从CSV文件导入韩文歌曲
        if csv_file_path:
            self.stdout.write(self.style.SUCCESS(f'开始从文件 {csv_file_path} 导入韩文歌曲...'))
            try:
                with open(csv_file_path, 'r', encoding=encoding) as f:
                    # 处理CSV导入
                    self.stdout.write(self.style.SUCCESS('导入功能尚未实现，请使用import_songs命令导入歌曲'))
            except UnicodeDecodeError:
                self.stdout.write(self.style.ERROR(f'无法使用 {encoding} 编码读取文件。请尝试其他编码，如 gbk, utf-8-sig, cp936 等'))
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'文件不存在：{csv_file_path}')) 