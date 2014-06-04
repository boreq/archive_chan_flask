import datetime

from django.utils.timezone import utc
from django.db.models import Count

from archive_chan.models import Board, Thread, Post
from archive_chan.settings import AppSettings


def get_stats(**kwargs):
    board_name = kwargs.get('board', None)
    thread_number = kwargs.get('thread', None)

    context = {}

    # This time is used when selecting data for a chart and recent posts.
    # It is supposed to prevent drawing to much data on the chart and ensures correct results when calculating posts per hour
    # (saved threads which do not get deleted would alter the results).
    timespan = AppSettings.get('RECENT_POSTS_AGE')
    timespan_time = datetime.datetime.now().replace(tzinfo=utc) - datetime.timedelta(hours=timespan)

    queryset_posts = Post.objects
    queryset_threads = Thread.objects

    if board_name is not None:
        queryset_posts = queryset_posts.filter(thread__board=board_name)
        queryset_threads = queryset_threads.filter(board=board_name)

    if thread_number is not None:
        queryset_posts = queryset_posts.filter(thread__number=thread_number)
        queryset_threads = queryset_threads.filter(number=thread_number)

    # Prepare data for the chart. It is necessary to convert it to a format required by Google Charts.
    posts = queryset_posts.filter(time__gt=timespan_time).extra({
        'date': 'date("time")',
        'hour': "date_part(\'hour\', \"time\")"
    }).values('date', 'hour').order_by('date', 'hour').annotate(amount=Count('id')).filter()
    context['chart_data'] = get_posts_chart_data(posts)

    # Posts.
    context['total_posts'] = queryset_posts.count()
    context['total_image_posts'] = queryset_posts.exclude(image=None).count()

    context['recent_posts'] = queryset_posts.filter(time__gt=timespan_time).count()
    context['recent_posts_timespan'] = timespan

    # Threads.
    context['total_threads'] = queryset_threads.count()

    return context

def get_posts_chart_data(queryset):
    """Creates data structured as required by Google Charts."""
    chart_data = {
        'cols': [{'label': 'Date', 'type': 'datetime'}, {'label': 'Posts', 'type': 'number'}],
        'rows': []
    }

    for entry in queryset:
        entry_time = datetime.datetime.combine(
            entry['date'],
            datetime.time(hour=int(entry['hour']))
        )

        value_string = format("Date(%s, %s, %s, %s, %s, %s)" % (
            entry_time.year,
            entry_time.month - 1, # JavaScript months start at 0.
            entry_time.day,
            entry_time.hour,
            entry_time.minute,
            entry_time.second
        ))

        label_string = entry_time.strftime('%Y-%m-%d %H:%M')

        chart_data['rows'].append({
            'c': [{'v': value_string, 'f': label_string}, {'v': entry['amount']}]
        })

    return chart_data
