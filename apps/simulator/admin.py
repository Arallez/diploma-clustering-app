from django.contrib import admin
from .models import Task, TaskTag, UserTaskAttempt

@admin.register(TaskTag)
class TaskTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'tags', 'difficulty', 'order')
    list_filter = ('tags', 'difficulty')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('tags__order', 'order')

@admin.register(UserTaskAttempt)
class UserTaskAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'task__title')
    readonly_fields = ('code', 'error_message', 'created_at')
