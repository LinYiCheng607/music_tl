from django.contrib import admin
from .models import Comment, Tag, Scene

# Register your models here.
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['comment_id', 'song', 'comment_user', 'comment_date', 'rating', 'emotion', 'get_tags_display', 'get_scenes_display']
    search_fields = ['song__song_name', 'comment_user', 'comment_text']
    list_filter = ['rating', 'emotion']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']

@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
