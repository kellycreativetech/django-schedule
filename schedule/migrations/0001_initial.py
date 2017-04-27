# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forms', '0002_auto_20160418_0120'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendee',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confirmation_code', models.CharField(max_length=16, db_index=True)),
                ('stripe_transaction', models.CharField(db_index=True, max_length=64, null=True, blank=True)),
                ('payment_exception', models.BooleanField(default=False)),
                ('attending', models.BooleanField(default=True, db_index=True)),
                ('wait_list', models.BooleanField(default=False, db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=64)),
                ('phone', models.CharField(default=b'', max_length=64, blank=True)),
                ('email', models.EmailField(default=b'', max_length=64, blank=True)),
                ('entry', models.ForeignKey(blank=True, to='forms.FormEntry', null=True)),
            ],
            options={
                'ordering': ['-wait_list', 'attending', 'created'],
            },
        ),
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(max_length=200, verbose_name='slug')),
            ],
            options={
                'verbose_name': 'calendar',
                'verbose_name_plural': 'calendar',
            },
        ),
        migrations.CreateModel(
            name='CalendarRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField()),
                ('distinction', models.CharField(max_length=20, null=True, verbose_name='distinction')),
                ('inheritable', models.BooleanField(default=True, verbose_name='inheritable')),
                ('calendar', models.ForeignKey(verbose_name='calendar', to='schedule.Calendar')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'calendar relation',
                'verbose_name_plural': 'calendar relations',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(help_text='The end time must be later than the start time.', verbose_name='end')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('created_on', models.DateTimeField(default=datetime.datetime.now, verbose_name='created on')),
                ('end_recurring_period', models.DateTimeField(help_text='This date is ignored for one time only events.', null=True, verbose_name='end recurring period', blank=True)),
                ('image', models.ImageField(null=True, upload_to=b'event_imgs', blank=True)),
                ('rsvp_requested', models.BooleanField(default=False, help_text=b'Check this box to include an RSVP form on this event')),
                ('max_attendees', models.IntegerField(default=None, help_text=b'Leave blank for unlimited attendees.', null=True, blank=True)),
                ('entrycost', models.DecimalField(decimal_places=2, max_digits=6, blank=True, help_text='This is the cost to be paid at the door on the day of the event.', null=True, verbose_name=b'Entry Cost')),
                ('rsvpcost', models.DecimalField(decimal_places=2, max_digits=6, blank=True, help_text='This is the cost to be paid online for the RSVP to be saved. If there is no RSVP Cost, a credit card form will not be displayed.', null=True, verbose_name=b'RSVP Cost')),
                ('calendar', models.ForeignKey(blank=True, to='schedule.Calendar', null=True)),
                ('creator', models.ForeignKey(verbose_name='creator', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('rsvp_form', models.ForeignKey(blank=True, to='forms.Form', null=True)),
            ],
            options={
                'get_latest_by': 'start',
                'verbose_name': 'event',
                'verbose_name_plural': 'events',
            },
        ),
        migrations.CreateModel(
            name='EventRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField()),
                ('distinction', models.CharField(max_length=20, null=True, verbose_name='distinction')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('event', models.ForeignKey(verbose_name='event', to='schedule.Event')),
            ],
            options={
                'verbose_name': 'event relation',
                'verbose_name_plural': 'event relations',
            },
        ),
        migrations.CreateModel(
            name='Occurrence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, null=True, verbose_name='title', blank=True)),
                ('description', models.TextField(null=True, verbose_name='description', blank=True)),
                ('start', models.DateTimeField(verbose_name='start')),
                ('end', models.DateTimeField(verbose_name='end')),
                ('cancelled', models.BooleanField(default=False, verbose_name='cancelled')),
                ('original_start', models.DateTimeField(verbose_name='original start')),
                ('original_end', models.DateTimeField(verbose_name='original end')),
                ('event', models.ForeignKey(verbose_name='event', to='schedule.Event')),
            ],
            options={
                'verbose_name': 'occurrence',
                'verbose_name_plural': 'occurrences',
            },
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, verbose_name='name')),
                ('description', models.TextField(verbose_name='description')),
                ('frequency', models.CharField(max_length=10, verbose_name='frequency', choices=[(b'YEARLY', 'Yearly'), (b'MONTHLY', 'Monthly'), (b'WEEKLY', 'Weekly'), (b'DAILY', 'Daily'), (b'HOURLY', 'Hourly'), (b'MINUTELY', 'Minutely'), (b'SECONDLY', 'Secondly')])),
                ('params', models.TextField(null=True, verbose_name='params', blank=True)),
            ],
            options={
                'verbose_name': 'rule',
                'verbose_name_plural': 'rules',
            },
        ),
        migrations.AddField(
            model_name='event',
            name='rule',
            field=models.ForeignKey(blank=True, to='schedule.Rule', help_text="Select '----' for a one time only event.", null=True, verbose_name='rule'),
        ),
        migrations.AddField(
            model_name='attendee',
            name='occurrence',
            field=models.ForeignKey(to='schedule.Occurrence'),
        ),
        migrations.AddField(
            model_name='attendee',
            name='parent',
            field=models.ForeignKey(blank=True, to='schedule.Attendee', null=True),
        ),
    ]
