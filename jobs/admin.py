from django.contrib import admin

from jobs.models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'assigned_recruiter', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'assigned_recruiter__username', 'assigned_recruiter__email')
    list_select_related = ('assigned_recruiter',)
    readonly_fields = ('created_at', 'updated_at')
