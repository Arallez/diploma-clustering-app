from django.contrib import admin
from .models import Material

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'concept', 'order', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('concept',)
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'content', 'order', 'concept')}),
        ('Связи', {'fields': ('tags',)}),
    )
    filter_horizontal = ('tags',)
