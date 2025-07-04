from django.db import models

# Create your models here.


# 歌曲分类表
class Label(models.Model):
    label_id = models.AutoField('序号', primary_key=True)
    label_name = models.CharField('分类标签', max_length=10)

    def __str__(self):
        return self.label_name

    class Meta:
        verbose_name = '歌曲分类'
        verbose_name_plural = '歌曲分类'


# 歌曲信息表
class Song(models.Model):
    song_id = models.AutoField('序号', primary_key=True)
    song_name = models.CharField('歌名', max_length=200)
    song_singer = models.CharField('歌手', max_length=100)
    song_time = models.CharField('时长', max_length=10)
    song_album = models.CharField('专辑', max_length=200)
    song_languages = models.CharField('语种', max_length=20)
    song_type = models.CharField('类型', max_length=20)
    song_release = models.CharField('发行时间', max_length=20)
    song_img = models.FileField('歌曲图片', upload_to='songImg', max_length=255)
    song_img_url = models.URLField('图片链接', max_length=500, blank=True, null=True)
    song_lyrics = models.FileField('歌词', upload_to='songLyric', max_length=255, default='暂无歌词')
    lyrics_text = models.TextField('歌词内容', blank=True, null=True)
    emotion_label = models.CharField(max_length=20, choices=[('happy', '开心'), ('sad', '伤感'), ('neutral', '中性')], null=True, blank=True, help_text='歌词情感标签')
    song_file = models.FileField('歌曲文件', upload_to='songFile', max_length=255)
    label = models.ForeignKey(Label, on_delete=models.CASCADE)

    def __str__(self):
        return self.song_name

    class Meta:
        verbose_name = '歌曲信息'
        verbose_name_plural = '歌曲信息'


# 歌曲动态表
class Dynamic(models.Model):
    dynamic_id = models.AutoField('序号', primary_key=True)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌名')
    dynamic_plays = models.IntegerField('播放次数')
    dynamic_search = models.IntegerField('搜索次数')
    dynamic_down = models.IntegerField('下载次数')

    class Meta:
        verbose_name = '歌曲动态'
        verbose_name_plural = '歌曲动态'


# 歌曲评论表
class Comment(models.Model):
    comment_id = models.AutoField('序号', primary_key=True)
    comment_text = models.CharField('内容', max_length=500)
    comment_user = models.CharField('用户', max_length=20)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌名')
    comment_date = models.CharField('日期', max_length=50)

    class Meta:
        verbose_name = '歌曲评论'
        verbose_name_plural = '歌曲评论'


