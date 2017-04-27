from django import forms
from django.utils.translation import ugettext_lazy as _
from schedule.models import Event, Occurrence, Rule, Attendee
from schedule.fields import DateTimeField
import datetime
import time


class SpanForm(forms.ModelForm):

    start = DateTimeField()
    end = DateTimeField(help_text=_("The end time must be later than start time."))

    def clean_end(self):
        if self.cleaned_data['end'] <= self.cleaned_data['start']:
            raise forms.ValidationError(_("The end time must be later than start time."))
        return self.cleaned_data['end']


class EventForm(SpanForm):
    def __init__(self, hour24=False, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)

    end_recurring_period = DateTimeField(help_text=_("This date is ignored for one time only events."), required=False)

    class Meta:
        model = Event
        exclude = ('creator', 'created_on', 'calendar')


class EventAdminForm(SpanForm):
    # end_recurring_period = DateTimeField(help_text=_("This date is ignored for one time only events."), required=False)

    class Meta:
        model = Event
        from django import VERSION
        if VERSION[1] in (7,8,9,10):
            fields = "__all__"


class OccurrenceForm(SpanForm):

    class Meta:
        model = Occurrence
        exclude = ('original_start', 'original_end', 'event', 'cancelled')


class RuleForm(forms.ModelForm):
    params = forms.CharField(widget=forms.Textarea, help_text=_("Extra parameters to define this type of recursion. Should follow this format: rruleparam:value;otherparam:value."))

    def clean_params(self):
        params = self.cleaned_data["params"]
        try:
            Rule(params=params).get_params()
        except (ValueError, SyntaxError):
            raise forms.ValidationError(_("Params format looks invalid"))
        return self.cleaned_data["params"]


class AttendeeForm(forms.Form):
    name = forms.CharField()
    phone = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    use_stripe = False

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.occurrence = kwargs.pop('occurrence', None)
        super(AttendeeForm, self).__init__(*args, **kwargs)

        if self.event and self.event.rsvpcost:
            self.use_stripe = True
            self.fields['email'].required = True

            self.fields['stripeEmail'] = self.fields['email']
            self.fields['stripeEmail'].label = "Email"
            self.fields['stripeEmail'].widget = forms.HiddenInput()
            del self.fields['email']

            self.fields['stripeToken'] = forms.CharField(widget=forms.HiddenInput)



class ModifyAttendanceForm(forms.ModelForm):
    attending = forms.TypedChoiceField(
        coerce=lambda x: x == 'True',
        choices=((False, 'Sorry, I need to cancel my RSVP for this event'), (True, 'I plan on attending this event')),
        widget=forms.RadioSelect
    )

    class Meta:
        model = Attendee
        fields = [
            'attending',
        ]
