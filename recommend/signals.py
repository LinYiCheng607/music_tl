from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from user.models import SongLog
from recommend.views import train_als_model

@receiver(post_save, sender=SongLog)
def trigger_model_training_on_interactions(sender, instance, created, **kwargs):
    if created:
        # 使用缓存跟踪交互计数
        interaction_count = cache.get('als_interaction_counter', 0) + 1
        cache.set('als_interaction_counter', interaction_count)
        
        # 当交互达到阈值时触发训练 (例如10次新交互)
        if interaction_count >= 10:
            train_als_model()
            cache.set('als_interaction_counter', 0)  # 重置计数器
            print(f"ALS模型已自动更新，触发条件: {interaction_count}次新交互")