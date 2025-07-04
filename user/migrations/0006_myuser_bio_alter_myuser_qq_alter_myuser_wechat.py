# Generated by Django 5.2.1 on 2025-06-26 02:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0005_myuser_nickname"),
    ]

    operations = [
        migrations.AddField(
            model_name="myuser",
            name="bio",
            field=models.CharField(
                blank=True, default="", max_length=100, verbose_name="个人签名"
            ),
        ),
        migrations.AlterField(
            model_name="myuser",
            name="qq",
            field=models.CharField(
                blank=True, default="", max_length=20, verbose_name="QQ号码"
            ),
        ),
        migrations.AlterField(
            model_name="myuser",
            name="weChat",
            field=models.CharField(
                blank=True, default="", max_length=20, verbose_name="微信号"
            ),
        ),
    ]
