from django.contrib import admin
from schedule.forms import RuleForm, EventAdminForm
from django.db import models
from django.conf import settings

from schedule.models import Calendar, Event, CalendarRelation, Rule, Occurrence

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

admin.site.register(Calendar, CalendarAdminOptions)
admin.site.register(Rule, RuleAdmin)
admin.site.register(CalendarRelation)
admin.site.register(Event, EventAdmin)
admin.site.register(Occurrence, OccurrenceAdmin)
