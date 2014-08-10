import json
from flask import Response, request
from flask.views import View
from flask.ext.login import current_user
from ..database import db
from ..models import Board, Thread, Post, Image, Tag, TagToThread
from ..lib import stats, helpers


class ApiError(Exception):
    def __init__(self, status_code=500, error_code='unknown',
                 message='Unknown server error.'):
        self.status_code = status_code
        self.error_code = error_code
        super(ApiError, self).__init__(message)


class NotImplementedApiError(ApiError):
    def __init__(self, **kwargs):
        status_code = kwargs.get('status_code', 501)
        error_code = kwargs.get('error_code', 'not_implemented')
        message = kwargs.get('message', 'Not implemented.')
        super(NotImplementedApiError, self).__init__(
            status_code,
            error_code,
            message
        )


class ApiView(View):
    methods = ['GET']

    def handle_exception(self, exception):
        """Extract exception parameters."""
        response_data = {
            'error_code': exception.error_code,
            'message': str(exception),
        }
        return (response_data, exception.status_code)

    def dispatch_request(self, *args, **kwargs):
        """Picks the right method and handles the exceptions.
        This view will try to get the data from <method_name>_api_response().
        """
        try:
            attr_name = request.method.lower() + '_api_response'
            if request.method in self.methods and hasattr(self, attr_name):
                response_data = getattr(self, attr_name)(*args, **kwargs)
                status_code = 200
            else:
                return self.http_method_not_allowed(request, *args, **kwargs)

        # Handle the exceptions thorown on purpose.
        except ApiError as e:
            response_data, status_code = self.handle_exception(e)

        # Handle other exceptions.
        except Exception as e:
            raise
            response_data, status_code = self.handle_exception(ApiError())

        return Response(json.dumps(response_data, indent=4),
            mimetype='application/json',
            status=status_code
        )
'''
class StatusView(ApiView):
    def get_chart_data(self, queryset):
        """Creates data structured as required by Google Charts."""
        chart_data = {
            'cols': [{'label': 'Date', 'type': 'datetime'}, {'label': 'Time per post', 'type': 'number'}],
            'rows': []
        }

        if queryset is None:
            return chart_data

        for entry in queryset:
            value_string = format("Date(%s, %s, %s, %s, %s, %s)" % (
                entry['date'].year,
                entry['date'].month - 1, # JavaScript months start at 0.
                entry['date'].day,
                0,
                0,
                0
            ))

            label_string = entry['date'].strftime('%Y-%m-%d')

            if entry['average_posts'] != 0:
                value = round(entry['average_time'] / entry['average_posts'], 3)
            else:
                value = 0

            chart_data['rows'].append({
                'c': [
                    {'v': value_string, 'f': label_string},
                    {'v': value},
                ]
            })

        return chart_data

    def get_api_response(self,  *args, **kwargs):
        response_data = {}

        # Last updates.
        last_updates = Update.objects.order_by('board__name', '-start').distinct('board').select_related('board')

        response_data['last_updates'] = [{
            'board': str(update.board),
            'start': update.start.isoformat(),
            'end': update.end.isoformat() if update.end else None,
            'status': update.status,
            'status_verbose': update.get_status_display(),
        } for update in last_updates]

        # Chart data.
        updates = Update.objects.filter(status=Update.COMPLETED).extra({
            'date': 'date("end")'
        }).values('date').order_by('date').annotate(
            average_time=Avg('total_time'),
            average_posts=Avg('added_posts')
        )

        response_data['chart_data'] = self.get_chart_data(updates)

        return response_data
'''


class StatsView(ApiView):
    def get_api_response(self, *args, **kwargs):
        return stats.get_stats(
            board_name=request.args.get('board'),
            thread_number=request.args.get('thread')
        )


class GalleryView(ApiView):
    def get_api_response(self, *args, **kwargs):
        board_name = request.args.get('board')
        thread_number = request.args.get('thread')
        last = request.args.get('last')
        amount = int(request.args.get('amount', 10))

        queryset = Image.query.join(Post, Thread, Board)
        
        if board_name:
            queryset = queryset.filter(
                Board.name==board_name
            )

        if thread_number:
            queryset = queryset.filter(
                Thread.number==thread_number
            )

        if last:
            queryset = queryset.filter(
                Image.id<last
            )

        queryset = queryset.order_by(Image.id.desc()).limit(amount)

        return {
            'images': [{
                'id': image.id,
                'board': image.post.thread.board.name,
                'thread': image.post.thread.number,
                'post': image.post.number,
                'extension': image.get_extension(),
                'url': image.image_url,
                'post_url': image.post.get_absolute_url()        
            } for image in queryset]
        }


def ajax_save_thread():
    """View used for AJAX save thread calls."""
    response = {}

    if current_user.is_authenticated():
        try:
            thread_number = int(request.form['thread'])
            board_name = request.form['board']
            state = (request.form['state'] == 'true')

            thread = Thread.query.join(Board).filter(
                Board.name==board_name,
                Thread.number==thread_number
            ).one()
            thread.saved = state
            db.session.commit()

            response = {
                'state': thread.saved
            }

        except:
            response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Not authorized.'
        }

    return Response(json.dumps(response), mimetype='application/json')


def ajax_get_parent_thread():
    """Returns a number of a thread the specified post belongs to."""
    response = {}

    try:
        post_number = int(request.form['post'])
        board_name = request.form['board']

        parent_thread_number = Post.objects.join(Thread, Board).filter(
            Board.name==board_name,
            Thread.number==post_number
        ).one().thread.number

        response = {
            'parent_thread': parent_thread_number
        }

    except:
        response = {
            'error': 'Error.'
        }

    return Response(json.dumps(response), mimetype='application/json')


def ajax_suggest_tag():
    """View used for AJAX tag suggestions in the 'new tag' field in the thread view."""
    response = {}

    try:
        query = request.args['query']

        tags = Tag.query.filter(Tag.name.like('%' + query + '%')).limit(5)

        response = {
            'query': query, 
            'suggestions': [tag.name for tag in tags]
        }

    except:
        response = {
            'error': 'Error.'
        }

    return Response(json.dumps(response), mimetype='application/json')


def ajax_add_tag():
    """View used for adding a tag to a thread."""
    response = {}

    if current_user.is_authenticated():
        try:
            thread_number = int(request.form['thread'])
            board_name = request.form['board']
            tag = request.form['tag']

            thread = Thread.query.join(Board).filter(
                Thread.number==thread_number, 
                Board.name==board_name
            ).one()

            exists = TagToThread.query.join(Tag).filter(
                TagToThread.thread==thread,
                Tag.name==tag
            ).first() is not None
                
            if not exists:
                tag, created_new_tag = helpers.get_or_create(db.session, Tag,
                    name=tag
                )
                db.session.commit()
                thread.tags.append(tag)
                db.session.commit()
                added = True
            else:
                added = False

            response = {
                'added': added
            }

        except:
            response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Not authorized.'
        }

    return Response(json.dumps(response), mimetype='application/json')

def ajax_remove_tag():
    """View used to remove a tag related to a thread."""
    response = {}

    if current_user.is_authenticated():
        try:
            thread_number = int(request.form['thread'])
            board_name = request.form['board']
            tag = request.form['tag']

            tagtothread = TagToThread.query.join(Thread, Board, Tag).filter(
                Thread.number==thread_number, 
                Board.name==board_name,
                Tag.name==tag
            ).one()
            db.session.delete(tagtothread)
            db.session.commit()

            response = {
                'removed': True
            }

        except:
           response = {
                'error': 'Error.'
            }
    else:
        response = {
            'error': 'Not authorized.'
        }

    return Response(json.dumps(response), mimetype='application/json')
