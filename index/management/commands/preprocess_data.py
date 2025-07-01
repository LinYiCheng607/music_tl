from django.core.management.base import BaseCommand
from index.models import Song
from django.db import connection

class Command(BaseCommand):
    help = '清理Song模型中song_img_url为空的数据'

    def handle(self, *args, **options):
        empty_records = Song.objects.filter(
            song_img_url__isnull=True
        ) | Song.objects.filter(
            song_img_url=''
        )
        count = empty_records.count()
        if count > 0:
            # 获取要删除的歌曲ID列表
            song_ids = tuple(empty_records.values_list('song_id', flat=True))
            if song_ids:
                # 使用原始SQL删除关联的AI分析记录
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM ai_features_aianalysis WHERE song_id IN %s",
                        [song_ids]
                    )
                    # 删除关联的播放记录
                    cursor.execute(
                        "DELETE FROM play_playrecord WHERE song_id IN %s",
                        [song_ids]
                    )
                    # 删除关联的相似歌曲记录
                    cursor.execute(
                        "DELETE FROM index_similarsong WHERE base_song_id IN %s",
                        [song_ids]
                    )
                    cursor.execute(
                        "DELETE FROM index_similarsong WHERE similar_song_id IN %s",
                        [song_ids]
                    )
            # 删除歌曲记录
            empty_records.delete()
            self.stdout.write(self.style.SUCCESS(f'成功清理 {count} 条无效记录及其关联数据'))
        else:
            self.stdout.write(self.style.SUCCESS('没有需要清理的记录'))