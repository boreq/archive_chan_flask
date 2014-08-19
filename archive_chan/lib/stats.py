import datetime
from flask import current_app
from ..models import Board, Thread, Post, Image
from ..database import db


def get_stats(board_name=None, thread_number=None):
    criterions = []
    if board_name is not None:
        criterions.append(Board.name==board_name)
    if thread_number is not None:
        criterions.append(Thread.number==thread_number)

    queryset_posts = Post.query.join(Thread, Board).filter(*criterions)
    queryset_threads = Thread.query.join(Board).filter(*criterions)

    # Time between the last and first post [hours] used when selecting data
    # for a chart and recent posts. Prevents displaying unreadable amount
    # of data. Ensures correct results when calculating posts per hour
    # (old saved threads which do not get deleted would alter the results).
    timespan = current_app.config['RECENT_POSTS_AGE']

    # Select all data in the thread mode.
    if board_name and thread_number:
        times = db.session.query(
            db.func.max(Post.time).label('last'), 
            db.func.min(Post.time).label('first'),
        ).join(Thread, Board).filter(*criterions).first()
        timespan = (times.last - times.first).total_seconds() / 3600

    # Calculate the time of the oldest post to select using the time of
    # the newest matched post. It would possible to get an empty chart
    # in the old threads if this wouid based on the current time.
    last_post_time = queryset_posts.order_by(Post.time.desc()).first().time
    first_post_time =  last_post_time - datetime.timedelta(hours=timespan)

    posts = db.session.query(
        db.func.count(Post.id).label('amount'),
        db.func.date(Post.time).label('date'),
        db.func.extract('hour', Post.time).label('hour')
    ).join(Thread, Board).group_by('date', 'hour').filter(
        Post.time>first_post_time,
        *criterions
    ).order_by('date', 'hour').all()

    context = {
        'total_threads': queryset_threads.count(),
        'total_posts': queryset_posts.count(),
        'total_image_posts': queryset_posts.join(Image).count(),
        'recent_posts': queryset_posts.filter(Post.time>first_post_time).count(),
        'recent_posts_timespan': timespan,
        'chart_data': get_posts_chart_data(posts),
    }
    return context


def get_posts_chart_data(queryset):
    """Creates data structured as required by Google Charts."""
    chart_data = {
        'cols': [
            {'label': 'Date', 'type': 'datetime'},
            {'label': 'Posts', 'type': 'number'}
        ],
        'rows': []
    }

    if queryset is None:
        return chart_data

    for entry in queryset:
        entry_time = datetime.datetime.combine(
            entry.date,
            datetime.time(hour=int(entry.hour))
        )

        value_string = 'Date(%s, %s, %s, %s, %s, %s)' % (
            entry_time.year,
            entry_time.month - 1, # JavaScript months start at 0.
            entry_time.day,
            entry_time.hour,
            entry_time.minute,
            entry_time.second
        )

        label_string = entry_time.strftime('%Y-%m-%d %H:%M')

        chart_data['rows'].append({
            'c': [
                {'v': value_string, 'f': label_string},
                {'v': entry.amount}
            ]
        })

    return chart_data
