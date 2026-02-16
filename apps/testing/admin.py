from django.contrib import admin
from .models import TeacherProfile, StudentGroup, GroupMembership, Test, TestAttempt


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'user__email')


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'join_code', 'teacher', 'created_at')
    list_filter = ('teacher',)
    search_fields = ('name', 'join_code')
    inlines = [GroupMembershipInline]


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'owner', 'time_limit_minutes', 'opens_at', 'closes_at')
    list_filter = ('group', 'owner')
    filter_horizontal = ('tasks',)


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'started_at', 'submitted_at')
    list_filter = ('test',)
