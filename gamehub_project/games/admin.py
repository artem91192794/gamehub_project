from django.contrib import admin
from .models import Category, Platform, Game

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ("name", "icon", "order", "is_active", "games_count")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    fieldsets = (
        ("Основная информация", {
            "fields": ("name", "slug", "icon", "description")
        }),
        ("Настройки", {
            "fields": ("order", "is_active")
        }),
    )
    
    def games_count(self, obj):
        """Отображает количество игр в категории"""
        return obj.get_games_count()
    games_count.short_description = "Игр"

@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "featured")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("category", "platforms", "featured")
    search_fields = ("title", "short_description", "description")
