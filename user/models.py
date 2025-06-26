from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from index.models import Song  # 跨应用导入Song模型

class MyUser(AbstractUser):
    nickname = models.CharField('昵称', max_length=30, blank=True, default='')
    qq = models.CharField('QQ号码', max_length=20, blank=True, default='')
    weChat = models.CharField('微信号', max_length=20, blank=True, default='')
    mobile = models.CharField('手机号码', max_length=11, unique=True)
    bio = models.CharField('个人签名', max_length=100, blank=True, default='')
    # 其他字段...

# 听歌记录表（已新增 song_type 和 song_languages 字段，信息和 Song 保持一致）
class SongLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌曲')
    listen_time = models.DateTimeField('听歌时间', auto_now_add=True)
    listen_count = models.PositiveIntegerField('听过的次数', default=1)
    total_listen_seconds = models.PositiveIntegerField('总听歌时长(秒)', default=0)
    song_type = models.CharField('类型', max_length=20)
    song_languages = models.CharField('语种', max_length=20, default='中文')

    class Meta:
        verbose_name = '听歌记录'
        verbose_name_plural = '听歌记录'

    def save(self, *args, **kwargs):
        # 自动从关联的 Song 表同步 song_type 和 song_languages 字段
        if self.song:
            self.song_type = self.song.song_type
            self.song_languages = self.song.song_languages
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} 听 {self.song}（{self.listen_count}次）"