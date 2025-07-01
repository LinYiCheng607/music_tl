from django.core.management.base import BaseCommand
from recommend.views import train_als_model

class Command(BaseCommand):
    help = '触发ALS推荐模型的训练和更新'

    def handle(self, *args, **options):
        self.stdout.write('开始训练ALS模型...')
        try:
            train_als_model()
            self.stdout.write(self.style.SUCCESS('ALS模型训练完成并已更新'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'模型训练失败: {str(e)}'))