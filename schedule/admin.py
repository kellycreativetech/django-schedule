from django.contrib import admin
from schedule.forms import RuleForm, EventAdminForm
from django.db import models
from django.conf import settings

from schedule.models import Calendar, Event, CalendarRelation, Rule, Attendee, Occurrence


from schedule.conf.settings import USE_ATTENDEES

class OccurrenceAdmin(admin.ModelAdmin):

    list_display = [
        'title', 'start', 'end'
    ]


class CalendarAdminOptions(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']


class RuleAdmin(admin.ModelAdmin):
    form = RuleForm


class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    list_display = [
        'title',
        'start',
    ]

class AttendeeAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'email',
        'phone',
        'confirmation_code',
        'occurrence',
        'stripe_url',
    ]
    search_fields = [
        'name',
        'email',
        'stripe_transaction',
        'confirmation_code',
    ]
    readonly_fields = [
        'stripe_transaction',
        'confirmation_code',
    ]

    ## Deleting from this interface is a bad idea.
    def has_delete_permission(self, request, obj=None):
        return False

    def stripe_url(self, obj):
        if obj.stripe_transaction:
            return "<a class='btn btn-default btn-sm' href='%s'>See On Stripe</a>" % obj.stripe_url
        return ""
    stripe_url.allow_tags = True


admin.site.register(Calendar, CalendarAdminOptions)
admin.site.register(Rule, RuleAdmin)
admin.site.register(CalendarRelation)
admin.site.register(Event, EventAdmin)
admin.site.register(Occurrence, OccurrenceAdmin)

if USE_ATTENDEES:
    admin.site.register(Attendee, AttendeeAdmin)
