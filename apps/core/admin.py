from django.contrib import admin
from .models import Material

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'created_at')
    search_fields = ('title', 'content')
