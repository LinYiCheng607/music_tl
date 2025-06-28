from django.db import models
from index.models import Song


class ArtistSimilarity(models.Model):
    """歌手相似度模型，存储歌手间的相似度分数"""
    artist1 = models.CharField('歌手1', max_length=100)
    artist2 = models.CharField('歌手2', max_length=100)
    similarity_score = models.FloatField('相似度分数', default=0.0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '歌手相似度'
        verbose_name_plural = '歌手相似度'
        unique_together = ('artist1', 'artist2')  # 确保歌手对的唯一性

    def __str__(self):
        return f"{self.artist1} 与 {self.artist2} 的相似度: {self.similarity_score:.4f}"


class ItemSimilarity(models.Model):
    """物品相似度模型，存储歌曲间的相似度分数"""
    song1 = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='similar_song1', verbose_name='歌曲1')
    song2 = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='similar_song2', verbose_name='歌曲2')
    similarity_score = models.FloatField('相似度分数', default=0.0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '物品相似度'
        verbose_name_plural = '物品相似度'
        unique_together = ('song1', 'song2')  # 确保歌曲对的唯一性

    def __str__(self):
        return f"{self.song1.song_name} 与 {self.song2.song_name} 的相似度: {self.similarity_score:.4f}"