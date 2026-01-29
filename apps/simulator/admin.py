from django.contrib import admin
from .models import Task, TaskCategory, UserTaskAttempt

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    ordering = ('order',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'algorithm', 'difficulty', 'order')
    list_filter = ('category', 'algorithm', 'difficulty')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('category__order', 'order')

@admin.register(UserTaskAttempt)
class UserTaskAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'task__title')
    readonly_fields = ('code', 'error_message', 'created_at')
