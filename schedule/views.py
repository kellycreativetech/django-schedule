from urllib import quote
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.views.generic.create_update import delete_object
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.generic.create_update import delete_object
import datetime

from schedule.conf.settings import GET_EVENTS_FUNC, OCCURRENCE_CANCEL_REDIRECT, USE_ATTENDEES
from schedule.forms import EventForm, OccurrenceForm, AttendeeForm
from schedule.models import *
from schedule.periods import weekday_names
from schedule.utils import check_event_permissions, coerce_date_dict

def calendar(request, calendar_slug, template='schedule/calendar.html', extra_context=None):
    """
    This view returns a calendar.  This view should be used if you are
    interested in the meta data of a calendar, not if you want to display a
    calendar.  It is suggested that you use calendar_by_periods if you would
    like to display a calendar.

    Context Variables:

    ``calendar``
        The Calendar object designated by the ``calendar_slug``.
    """
    extra_context = extra_context or {}
    calendar = get_object_or_404(Calendar, slug=calendar_slug)
    context = {"calendar": calendar}
    context.update(extra_context)
    return render_to_response(template, context, context_instance=RequestContext(request))

def calendar_by_periods(request, calendar_slug=None, periods=None,
    template_name="schedule/calendar_by_period.html", extra_context=None):
    """
    This view is for getting a calendar, but also getting periods with that
    calendar.  Which periods you get, is designated with the list periods. You
    can designate which date you the periods to be initialized to by passing
    a date in request.GET. See the template tag ``query_string_for_date``

    Context Variables

    ``date``
        This was the date that was generated from the query string.

    ``periods``
        this is a dictionary that returns the periods from the list you passed
        in.  If you passed in Month and Day, then your dictionary would look
        like this

        {
            'month': <schedule.periods.Month object>
            'day':   <schedule.periods.Day object>
        }

        So in the template to access the Day period in the context you simply
        use ``periods.day``.

    ``calendar``
        This is the Calendar that is designated by the ``calendar_slug``.

    ``weekday_names``
        This is for convenience. It returns the local names of weekedays for
        internationalization.

    """
    extra_context = extra_context or {}

    if calendar_slug:
        calendar = get_object_or_404(Calendar, slug=calendar_slug)
        event_list = GET_EVENTS_FUNC(request, calendar)
    else:
        calendar = None
        event_list = Event.objects.all()

    date = coerce_date_dict(request.GET)
    if date:
        try:
            date = datetime.datetime(**date)
        except ValueError:
            raise Http404
    else:
        date = datetime.datetime.now()
    period_objects = dict([(period.__name__.lower(), period(event_list, date)) for period in periods])
    context = {
            'date': date,
            'periods': period_objects,
            'calendar': calendar,
            'weekday_names': weekday_names,
            'here':quote(request.get_full_path()),
        }
    context.update(extra_context)
    return render_to_response(template_name, context, context_instance=RequestContext(request),)

def event(request, event_id, template_name="schedule/event.html", extra_context=None):
    """
    This view is for showing an event. It is important to remember that an
    event is not an occurrence.  Events define a set of reccurring occurrences.
    If you would like to display an occurrence (a single instance of a
    recurring event) use occurrence.

    Context Variables:

    event
        This is the event designated by the event_id

    back_url
        this is the url that referred to this view.
    """
    extra_context = extra_context or {}
    event = get_object_or_404(Event, id=event_id)
    back_url = request.META.get('HTTP_REFERER', None)
    try:
        cal = event.calendar_set.get()
    except:
        cal = None
    context = {
        "event": event,
        "back_url" : back_url,
    }
    context.update(extra_context)
    return render_to_response(template_name, context, context_instance=RequestContext(request))

def occurrence(request, event_id,
    template_name="schedule/occurrence.html", *args, **kwargs):
    """
    This view is used to display an occurrence.

    Context Variables:

    ``event``
        the event that produces the occurrence

    ``occurrence``
        the occurrence to be displayed

    ``back_url``
        the url from which this request was refered
    """
    extra_context = kwargs.get('extra_context', None) or {}
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    back_url = request.META.get('HTTP_REFERER', None)
    context =  {
        'event': event,
        'occurrence': occurrence,
        'back_url': back_url,
    }
    context.update(extra_context)

    if USE_ATTENDEES:
        form = AttendeeForm(event, occurrence, request.POST or None)
        amount = int(event.rsvpcost * 100)
        if form.is_valid():
            # Save Occurrence, in case it has not been persisted yet.
            occurrence.save()

            # Save Attendee
            attendee = Attendee(
                occurrence=occurrence,
                name=form.cleaned_data['name'],
                email=form.cleaned_data.get('email', None) or form.cleaned_data['stripeEmail'],
                phone=form.cleaned_data['phone']
            )
            attendee.save()

            if amount:
                import stripe
                # Charge Credit Card
                card = stripe.Token.retrieve(form.cleaned_data['stripeToken'])

                charge_obj = stripe.Charge.create(
                  amount=amount,
                  currency="usd",
                  card=card,
                  description="RSVP %s" % occurrence.title,
                  metadata={},
                )

                # Save Attendee Again
                attendee.stripe_transaction = charge_obj.id
                attendee.save()

                # Do some stuff? Email the individual a reciept? Show them their confirmation code.

            # Return Redirect
            return redirect(request.get_full_path())

        context.update({
            "form": form,
            "amount": amount,
        })


    return render_to_response(template_name, context, context_instance=RequestContext(request))


@check_event_permissions
def edit_occurrence(request, event_id,
    template_name="schedule/edit_occurrence.html", *args, **kwargs):
    extra_context = kwargs.get('extra_context', None) or {}
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    next = kwargs.get('next', None)
    form = OccurrenceForm(data=request.POST or None, instance=occurrence)
    if form.is_valid():
        occurrence = form.save(commit=False)
        occurrence.event = event
        occurrence.save()
        next = next or get_next_url(request, occurrence.get_absolute_url())
        return HttpResponseRedirect(next)
    next = next or get_next_url(request, occurrence.get_absolute_url())
    context = {
        'form': form,
        'occurrence': occurrence,
        'next':next,
    }
    context.update(extra_context)
    return render_to_response(template_name, context, context_instance=RequestContext(request))


@check_event_permissions
def cancel_occurrence(request, event_id,
    template_name='schedule/cancel_occurrence.html', *args, **kwargs):
    """
    This view is used to cancel an occurrence. If it is called with a POST it
    will cancel the view. If it is called with a GET it will ask for
    conformation to cancel.
    """
    extra_context = kwargs.get('extra_context', None) or {}
    event, occurrence = get_occurrence(event_id, *args, **kwargs)
    next = kwargs.get('next',None) or get_next_url(request, event.get_absolute_url())
    if request.method != "POST":
        context = {
            "occurrence": occurrence,
            "next":next,
        }
        context.update(extra_context)
        return render_to_response(template_name, context, context_instance=RequestContext(request))
    occurrence.cancel()
    return HttpResponseRedirect(next)


def get_occurrence(event_id, occurrence_id=None, year=None, month=None,
    day=None, hour=None, minute=None, second=None):
    """
    Because occurrences don't have to be persisted, there must be two ways to
    retrieve them. both need an event, but if its persisted the occurrence can
    be retrieved with an id. If it is not persisted it takes a date to
    retrieve it.  This function returns an event and occurrence regardless of
    which method is used.
    """
    if(occurrence_id):
        occurrence = get_object_or_404(Occurrence, id=occurrence_id)
        event = occurrence.event
    elif(all((year, month, day, hour, minute, second))):
        event = get_object_or_404(Event, id=event_id)
        occurrence = event.get_occurrence(
            datetime.datetime(int(year), int(month), int(day), int(hour),
                int(minute), int(second)))
        if occurrence is None:
            raise Http404
    else:
        raise Http404
    return event, occurrence


@check_event_permissions
def create_or_edit_event(request, calendar_slug, event_id=None, next=None,
    template_name='schedule/create_event.html', form_class = EventForm, extra_context=None):
    """
    This function, if it receives a GET request or if given an invalid form in a
    POST request it will generate the following response

    Template:
        schedule/create_event.html

    Context Variables:

    form:
        an instance of EventForm

    calendar:
        a Calendar with id=calendar_id

    if this function gets a GET request with ``year``, ``month``, ``day``,
    ``hour``, ``minute``, and ``second`` it will auto fill the form, with
    the date specifed in the GET being the start and 30 minutes from that
    being the end.

    If this form receives an event_id it will edit the event with that id, if it
    recieves a calendar_id and it is creating a new event it will add that event
    to the calendar with the id calendar_id

    If it is given a valid form in a POST request it will redirect with one of
    three options, in this order

    # Try to find a 'next' GET variable
    # If the key word argument redirect is set
    # Lastly redirect to the event detail of the recently create event
    """
    extra_context = extra_context or {}
    date = coerce_date_dict(request.GET)
    initial_data = None
    if date:
        try:
            start = datetime.datetime(**date)
            initial_data = {
                "start": start,
                "end": start + datetime.timedelta(minutes=30)
            }
        except TypeError:
            raise Http404
        except ValueError:
            raise Http404

    instance = None
    if event_id is not None:
        instance = get_object_or_404(Event, id=event_id)

    calendar = get_object_or_404(Calendar, slug=calendar_slug)

    form = form_class(data=request.POST or None, instance=instance,
        hour24=True, initial=initial_data)

    if form.is_valid():
        event = form.save(commit=False)
        if instance is None:
            event.creator = request.user
            event.calendar = calendar
        event.save()
        next = next or reverse('event', args=[event.id])
        next = get_next_url(request, next)
        return HttpResponseRedirect(next)

    next = get_next_url(request, next)
    context = {
        "form": form,
        "calendar": calendar,
        "next":next
    }
    context.update(extra_context)
    return render_to_response(template_name, context, context_instance=RequestContext(request))


@check_event_permissions
def delete_event(request, event_id, next=None, login_required=True, extra_context=None):
    """
    After the event is deleted there are three options for redirect, tried in
    this order:

    # Try to find a 'next' GET variable
    # If the key word argument redirect is set
    # Lastly redirect to the event detail of the recently create event
    """
    extra_context = extra_context or {}
    event = get_object_or_404(Event, id=event_id)
    next = next or reverse('day_calendar', args=[event.calendar.slug])
    next = get_next_url(request, next)
    extra_context['next'] = next
    return delete_object(request,
                         model = Event,
                         object_id = event_id,
                         post_delete_redirect = next,
                         template_name = "schedule/delete_event.html",
                         extra_context = extra_context,
                         login_required = login_required
                        )

def check_next_url(next):
    """
    Checks to make sure the next url is not redirecting to another page.
    Basically it is a minimal security check.
    """
    if not next or '://' in next:
        return None
    return next

def get_next_url(request, default):
    next = default
    if OCCURRENCE_CANCEL_REDIRECT:
        next = OCCURRENCE_CANCEL_REDIRECT
    if 'next' in request.REQUEST and check_next_url(request.REQUEST['next']) is not None:
        next = request.REQUEST['next']
    return next
