from django.core.management.base import BaseCommand
from index.models import Song
from snownlp import SnowNLP
import logging

logger = logging.getLogger(__name__)

def analyze_emotion(text):
    """使用SnowNLP分析文本情感，返回'happy'、'sad'或'neutral'"""
    if not text or text.strip() == '':
        return 'neutral'
    try:
        s = SnowNLP(text)
        sentiment = s.sentiments
        if sentiment > 0.8:
            return 'excited'
        elif 0.6 < sentiment < 0.8:
            return 'happy'
        elif 0.4 < sentiment < 0.6:
            return 'relaxed'
        elif 0.3 < sentiment < 0.4:
            return 'nostalgic'
        else:
            return 'sad'
    except Exception as e:
        logger.error(f"情感分析失败: {str(e)}")
        return 'relax'

class Command(BaseCommand):
    help = '批量处理所有歌曲的歌词情感标签并保存到数据库'

    def handle(self, *args, **options):
        # 获取所有未处理或需要更新的歌曲
        songs = Song.objects.all()
        total = songs.count()
        processed = 0
        updated = 0

        self.stdout.write(f"开始处理{total}首歌曲的歌词情感标签...")

        for song in songs:
            processed += 1
            # 跳过没有歌词的歌曲
            if not song.lyrics_text or song.lyrics_text.strip() == '':
                self.stdout.write(f"[{processed}/{total}] 歌曲 '{song.song_name}' 无歌词，跳过")
                continue

            # 分析情感
            emotion = analyze_emotion(song.lyrics_text)

            # 如果情感标签有变化才保存
            if song.emotion_label != emotion:
                song.emotion_label = emotion
                song.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"[{processed}/{total}] 已更新歌曲 '{song.song_name}' 的情感标签为: {emotion}"))
            else:
                self.stdout.write(f"[{processed}/{total}] 歌曲 '{song.song_name}' 的情感标签未变化: {emotion}")

        self.stdout.write(self.style.SUCCESS(f"处理完成！共处理{processed}首歌曲，更新{updated}个情感标签"))