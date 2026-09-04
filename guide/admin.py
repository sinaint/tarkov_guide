from django.contrib import admin

from .models import TarkovItem


@admin.register(TarkovItem)
class TarkovItemAdmin(admin.ModelAdmin):
    """관리자 페이지에서 데이터가 잘 들어왔는지 확인할 때 씁니다."""
    list_display = ("name", "category", "avg_24h_price", "synced_at")
    list_filter = ("category",)
    search_fields = ("name", "short_name")
