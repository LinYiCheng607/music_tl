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

class SongLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='用户')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, verbose_name='歌曲')
    listen_time = models.DateTimeField('听歌时间', auto_now_add=True)
    listen_count = models.PositiveIntegerField('听过的次数', default=1)
    total_listen_seconds = models.PositiveIntegerField('总听歌时长(秒)', default=0)

    class Meta:
        verbose_name = '听歌记录'
        verbose_name_plural = '听歌记录'

    def __str__(self):
        return f"{self.user.username} 听 {self.song}（{self.listen_count}次）"