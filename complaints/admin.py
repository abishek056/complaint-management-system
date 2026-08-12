"""
Django admin customization for the Complaint Management System.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Category, Complaint, Comment, StatusHistory


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'profile__role')

    def get_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except Profile.DoesNotExist:
            return '-'
    get_role.short_description = 'Role'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'department', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('author', 'created_at')


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'created_at')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        'complaint_id_display', 'title', 'category', 'priority',
        'status', 'submitted_by', 'assigned_to', 'created_at'
    )
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description', 'submitted_by__username')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    list_editable = ('status', 'priority')
    date_hierarchy = 'created_at'
    inlines = [CommentInline, StatusHistoryInline]
    actions = ['mark_resolved', 'mark_in_progress']

    def complaint_id_display(self, obj):
        return obj.complaint_id
    complaint_id_display.short_description = 'ID'

    @admin.action(description='Mark selected as Resolved')
    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')

    @admin.action(description='Mark selected as In Progress')
    def mark_in_progress(self, request, queryset):
        queryset.update(status='in_progress')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'author', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at')


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status',)

# Admin site branding
admin.site.site_header = 'Complaint Management System'
admin.site.site_title = 'CMS Admin'
admin.site.index_title = 'Administration'
