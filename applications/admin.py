from django.contrib import admin

from applications.models import Application, ApplicationHistory


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'candidate', 'job', 'stage', 'version', 'created_at', 'updated_at')
    list_filter = ('stage', 'created_at')
    search_fields = (
        'candidate__username',
        'candidate__email',
        'job__title',
    )
    list_select_related = ('candidate', 'job')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ApplicationHistory)
class ApplicationHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'application',
        'actor',
        'previous_stage',
        'new_stage',
        'timestamp',
    )
    list_filter = ('previous_stage', 'new_stage', 'timestamp')
    search_fields = ('application__candidate__username', 'application__job__title', 'actor__username')
    list_select_related = ('application', 'actor', 'application__candidate', 'application__job')
    readonly_fields = (
        'application',
        'actor',
        'timestamp',
        'previous_stage',
        'new_stage',
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
