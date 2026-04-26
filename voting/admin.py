from django.contrib import admin
from .models import Region, Candidate, Voter, Vote, Alert, VoteAuditLog


admin.site.register(Region)
admin.site.register(Voter)
admin.site.register(Vote)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display  = ('name', 'party', 'region', 'age', 'occupation')
    list_filter   = ('party', 'region')
    search_fields = ('name', 'party')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'party', 'region'),
        }),
        ('Photos', {
            'fields': ('photo', 'cover_photo'),
        }),
        ('Profile & Biography', {
            'fields': ('slogan', 'bio', 'age', 'occupation'),
        }),
        ('Manifesto / Policy Points', {
            'description': 'Enter one policy point per line. Each line becomes a checklist item on the profile page.',
            'fields': ('manifesto',),
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display  = ('region', 'alert_time', 'resolved', 'short_message')
    list_filter   = ('resolved', 'region')
    ordering      = ('-alert_time',)
    actions       = ['mark_resolved']

    def short_message(self, obj):
        return obj.message[:80] + ('…' if len(obj.message) > 80 else '')
    short_message.short_description = 'Message'

    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)
    mark_resolved.short_description = 'Mark selected alerts as resolved'


@admin.register(VoteAuditLog)
class VoteAuditLogAdmin(admin.ModelAdmin):
    list_display  = ('voter', 'region_name', 'risk_score', 'flagged',
                     'flag_reason', 'hour_of_day', 'otp_attempts',
                     'time_since_otp_request', 'created_at')
    list_filter   = ('flagged', 'voter__region')
    ordering      = ('-risk_score', '-created_at')
    readonly_fields = (
        'voter', 'ip_address', 'user_agent', 'hour_of_day',
        'otp_attempts', 'time_since_otp_request',
        'risk_score', 'flagged', 'flag_reason', 'created_at',
    )
    search_fields = ('voter__voter_id', 'ip_address', 'flag_reason')

    def region_name(self, obj):
        return obj.voter.region.name
    region_name.short_description = 'Region'
    region_name.admin_order_field = 'voter__region__name'
