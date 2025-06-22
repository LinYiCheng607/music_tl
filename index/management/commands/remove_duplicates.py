from django.core.management.base import BaseCommand
from django.db.models import Count
from index.models import Song, Dynamic, Comment
from collections import defaultdict

class Command(BaseCommand):
    help = '检测并删除数据库中的重复记录'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='仅检测不删除')
        parser.add_argument('--model', type=str, default='all', help='指定要检查的模型(song, dynamic, comment, all)')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        model_type = options['model'].lower()
        
        if model_type in ['all', 'song']:
            self.check_duplicate_songs(dry_run)
        
        if model_type in ['all', 'dynamic']:
            self.check_duplicate_dynamics(dry_run)
        
        if model_type in ['all', 'comment']:
            self.check_duplicate_comments(dry_run)

    def check_duplicate_songs(self, dry_run):
        """检查并删除重复的歌曲记录"""
        self.stdout.write(self.style.NOTICE('正在检查重复的歌曲记录...'))
        
        # 按歌名和歌手分组，找出重复记录
        duplicates = Song.objects.values('song_name', 'song_singer').annotate(
            count=Count('song_id')
        ).filter(count__gt=1)
        
        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('没有发现重复的歌曲记录！'))
            return
        
        total_duplicates = 0
        removed = 0
        
        for duplicate in duplicates:
            song_name = duplicate['song_name']
            song_singer = duplicate['song_singer']
            
            # 获取所有匹配的记录，按ID排序
            songs = Song.objects.filter(
                song_name=song_name,
                song_singer=song_singer
            ).order_by('song_id')
            
            count = songs.count()
            total_duplicates += count - 1
            
            self.stdout.write(f'发现重复歌曲: {song_name} - {song_singer}, 共 {count} 条记录')
            
            if not dry_run:
                # 保留第一条记录，删除其余记录
                keep_song = songs.first()
                
                for song in songs[1:]:
                    # 将关联的Dynamic记录转移到保留的歌曲上
                    Dynamic.objects.filter(song=song).update(song=keep_song)
                    
                    # 将关联的Comment记录转移到保留的歌曲上
                    Comment.objects.filter(song=song).update(song=keep_song)
                    
                    # 删除重复的歌曲记录
                    song_id = song.song_id
                    song.delete()
                    removed += 1
                    self.stdout.write(f'  删除重复歌曲ID: {song_id}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'发现 {total_duplicates} 条重复歌曲记录（试运行模式，未删除）'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已删除 {removed} 条重复歌曲记录'))

    def check_duplicate_dynamics(self, dry_run):
        """检查并删除重复的歌曲动态记录"""
        self.stdout.write(self.style.NOTICE('正在检查重复的歌曲动态记录...'))
        
        # 按歌曲ID分组，找出重复记录
        song_dynamics = defaultdict(list)
        for dynamic in Dynamic.objects.all():
            song_dynamics[dynamic.song_id].append(dynamic)
        
        duplicates = {song_id: dynamics for song_id, dynamics in song_dynamics.items() if len(dynamics) > 1}
        
        if not duplicates:
            self.stdout.write(self.style.SUCCESS('没有发现重复的歌曲动态记录！'))
            return
        
        total_duplicates = 0
        removed = 0
        
        for song_id, dynamics in duplicates.items():
            count = len(dynamics)
            total_duplicates += count - 1
            
            self.stdout.write(f'发现歌曲ID {song_id} 的重复动态记录, 共 {count} 条')
            
            if not dry_run:
                # 按ID排序，保留第一条记录
                dynamics.sort(key=lambda x: x.dynamic_id)
                keep_dynamic = dynamics[0]
                
                # 合并播放、搜索、下载次数
                total_plays = sum(d.dynamic_plays for d in dynamics)
                total_search = sum(d.dynamic_search for d in dynamics)
                total_down = sum(d.dynamic_down for d in dynamics)
                
                keep_dynamic.dynamic_plays = total_plays
                keep_dynamic.dynamic_search = total_search
                keep_dynamic.dynamic_down = total_down
                keep_dynamic.save()
                
                # 删除其余记录
                for dynamic in dynamics[1:]:
                    dynamic_id = dynamic.dynamic_id
                    dynamic.delete()
                    removed += 1
                    self.stdout.write(f'  删除重复动态记录ID: {dynamic_id}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'发现 {total_duplicates} 条重复动态记录（试运行模式，未删除）'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已删除 {removed} 条重复动态记录'))

    def check_duplicate_comments(self, dry_run):
        """检查并删除重复的评论记录"""
        self.stdout.write(self.style.NOTICE('正在检查重复的评论记录...'))
        
        # 按评论内容、用户和歌曲ID分组，找出重复记录
        duplicates = Comment.objects.values('comment_text', 'comment_user', 'song').annotate(
            count=Count('comment_id')
        ).filter(count__gt=1)
        
        if not duplicates.exists():
            self.stdout.write(self.style.SUCCESS('没有发现重复的评论记录！'))
            return
        
        total_duplicates = 0
        removed = 0
        
        for duplicate in duplicates:
            comment_text = duplicate['comment_text']
            comment_user = duplicate['comment_user']
            song_id = duplicate['song']
            
            # 获取所有匹配的记录，按ID排序
            comments = Comment.objects.filter(
                comment_text=comment_text,
                comment_user=comment_user,
                song_id=song_id
            ).order_by('comment_id')
            
            count = comments.count()
            total_duplicates += count - 1
            
            self.stdout.write(f'发现重复评论: "{comment_text[:30]}..." - 用户: {comment_user}, 歌曲ID: {song_id}, 共 {count} 条')
            
            if not dry_run:
                # 保留第一条记录，删除其余记录
                for comment in comments[1:]:
                    comment_id = comment.comment_id
                    comment.delete()
                    removed += 1
                    self.stdout.write(f'  删除重复评论ID: {comment_id}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'发现 {total_duplicates} 条重复评论记录（试运行模式，未删除）'))
        else:
            self.stdout.write(self.style.SUCCESS(f'已删除 {removed} 条重复评论记录')) 