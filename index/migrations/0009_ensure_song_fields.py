from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('index', '0008_song_lyrics_text'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='song',
        #     name='song_languages',
        #     field=models.CharField(default='中文', max_length=20, verbose_name='语种'),
        #     preserve_default=False,
        # ),
        # migrations.AddField(
        #     model_name='song',
        #     name='song_type',
        #     field=models.CharField(default='流行', max_length=20, verbose_name='类型'),
        #     preserve_default=False,
        # ),
    ]