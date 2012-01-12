from django.contrib import admin
from schedule.forms import RuleForm
from django.db import models

from schedule.models import Calendar, Event, CalendarRelation, Rule
from schedule.widgets import JqSplitDateTimeWidget
from schedule.fields import JqSplitDateTimeField

class CalendarAdminOptions(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ['name']

class RuleAdmin(admin.ModelAdmin):
    form = RuleForm

class EventAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.DateTimeField: {'widget': JqSplitDateTimeField(widget=JqSplitDateTimeWidget(attrs={'date_class':'datepicker','time_class':'timepicker'}))},
    }

admin.site.register(Calendar, CalendarAdminOptions)
admin.site.register(Rule, RuleAdmin)
admin.site.register(CalendarRelation)
admin.site.register(Event, EventAdmin)
