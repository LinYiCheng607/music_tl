from django.core.management.base import BaseCommand
from index.models import Label

class Command(BaseCommand):
    help = '创建歌曲分类标签'

    def add_arguments(self, parser):
        parser.add_argument('label_name', type=str, help='标签名称')

    def handle(self, *args, **options):
        label_name = options['label_name']
        
        # 检查标签是否已存在
        if Label.objects.filter(label_name=label_name).exists():
            self.stdout.write(self.style.WARNING(f'标签 "{label_name}" 已存在'))
            return
        
        # 创建标签
        label = Label(label_name=label_name)
        label.save()
        
        self.stdout.write(self.style.SUCCESS(f'成功创建标签 "{label_name}"，ID为 {label.label_id}')) 