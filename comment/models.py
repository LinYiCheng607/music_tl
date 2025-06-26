from django.db import models
from index.models import Song

# Create your models here.

# 标签模型
class Tag(models.Model):
    name = models.CharField('标签名称', max_length=50)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '歌曲标签'
        verbose_name_plural = '歌曲标签'

# 场景模型
class Scene(models.Model):
    name = models.CharField('场景名称', max_length=50)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = '使用场景'
        verbose_name_plural = '使用场景'

# 情绪选项
EMOTION_CHOICES = (
    ('happy', '开心'),
    ('sad', '伤感'),
    ('excited', '兴奋'),
    ('relaxed', '放松'),
    ('nostalgic', '怀旧'),
    ('other', '其他'),
)

# 扩展的点评模型
class Comment(models.Model):
    comment_id = models.AutoField('序号', primary_key=True)
    comment_text = models.CharField('内容', max_length=500, blank=True, null=True)
    comment_user = models.CharField('用户', max_length=20)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌名', related_name='extended_comments')
    comment_date = models.CharField('日期', max_length=50)
    rating = models.IntegerField('评分', choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')], null=True)
    emotion = models.CharField('情感', max_length=20, choices=EMOTION_CHOICES, null=True)
    tags = models.ManyToManyField(Tag, verbose_name='标签', blank=True)
    scenes = models.ManyToManyField(Scene, verbose_name='适合场景', blank=True)

    class Meta:
        verbose_name = '歌曲点评'
        verbose_name_plural = '歌曲点评'
        
    def get_tags_display(self):
        return ", ".join([tag.name for tag in self.tags.all()])
    
    def get_scenes_display(self):
        return ", ".join([scene.name for scene in self.scenes.all()])
