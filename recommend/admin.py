from django.contrib import admin
from .models import ItemSimilarity


@admin.register(ItemSimilarity)
class ItemSimilarityAdmin(admin.ModelAdmin):
    list_display = ('id', 'song1', 'song2', 'similarity_score', 'updated_at')
    list_filter = ('updated_at',)
    search_fields = ('song1__song_name', 'song2__song_name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('song1', 'song2')