import json
from flask import Blueprint, Response, request
from flask.views import View
from flask.ext.login import current_user
from sqlalchemy.orm.exc import NoResultFound
from ..database import db
from ..models import Board, Thread, Post, Image, Tag, TagToThread, Update
from ..lib import stats, helpers


bl = Blueprint('api', __name__)


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


class MethodNotAllowedApiError(ApiError):
    def __init__(self, **kwargs):
        status_code = kwargs.get('status_code', 405)
        error_code = kwargs.get('error_code', 'method_not_allowed')
        message = kwargs.get('message', 'Method not allowed')
        super(MethodNotAllowedApiError, self).__init__(
            status_code,
            error_code,
            message
        )


class NotAuthorizedApiError(ApiError):
    def __init__(self, **kwargs):
        status_code = kwargs.get('status_code', 401)
        error_code = kwargs.get('error_code', 'unauthorized')
        message = kwargs.get('message', 'Log in.')
        super(MethodNotAllowedApiError, self).__init__(
            status_code,
            error_code,
            message
        )


class NotFoundApiError(ApiError):
    def __init__(self, **kwargs):
        status_code = kwargs.get('status_code', 404)
        error_code = kwargs.get('error_code', 'not_found')
        message = kwargs.get('message', 'Item could not be found.')
        super(NotFoundApiError, self).__init__(
            status_code,
            error_code,
            message
        )


class ApiView(View):
    methods = ['GET']

    def handle_exception(self, exception):
        """Converts exception to JSON response and status code."""
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
            if not request.method in self.methods:
                raise MethodNotAllowedApiError

            if hasattr(self, attr_name):
                response_data = getattr(self, attr_name)(*args, **kwargs)
                status_code = 200
            else:
                raise NotImplementedApiError

        # Handle the exceptions thrown on purpose.
        except ApiError as e:
            response_data, status_code = self.handle_exception(e)

        # Handle other exceptions.
        except Exception as e:
            response_data, status_code = self.handle_exception(ApiError())

        return Response(json.dumps(response_data, indent=4),
            mimetype='application/json',
            status=status_code
        )


class Status(ApiView):
    def get_chart_data(self, queryset):
        """Creates data structured as required by Google Charts."""
        chart_data = {
            'cols': [
                {'label': 'Date', 'type': 'datetime'},
                {'label': 'Time per post', 'type': 'number'}
            ],
            'rows': []
        }

        if queryset is None:
            return chart_data

        for entry in queryset:
            value_string = 'Date(%s, %s, %s, %s, %s, %s)' % (
                entry.date.year,
                entry.date.month - 1, # JavaScript months start at 0.
                entry.date.day,
                0,
                0,
                0
            )

            label_string = entry.date.strftime('%Y-%m-%d')

            if entry.average_posts != 0:
                value = round(entry.average_time / float(entry.average_posts), 3)
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
        last_updates = Update.query \
                             .join(Board) \
                             .order_by(Update.board_id, Update.start.desc()) \
                             .distinct(Update.board_id)

        response_data['last_updates'] = [{
            'board': str(update.board),
            'start': update.start.isoformat(),
            'end': update.end.isoformat() if update.end else None,
            'status': update.status,
            'status_verbose': update.get_status_display(),
        } for update in last_updates]

        # Chart data.
        updates = db.session.query(
            db.func.avg(Update.total_time).label('average_time'),
            db.func.avg(Update.added_posts).label('average_posts'),
            db.func.date(Update.end).label('date')
        ).filter(Update.status==Update.COMPLETED).group_by('date').order_by('date').all()

        response_data['chart_data'] = self.get_chart_data(updates)

        return response_data


class Stats(ApiView):
    def get_api_response(self, *args, **kwargs):
        return stats.get_stats(
            board_name=request.args.get('board'),
            thread_number=request.args.get('thread')
        )


class Gallery(ApiView):
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
                'post_url': image.post.get_absolute_url(),
            } for image in queryset]
        }


class SaveThread(ApiView):
    methods = ['POST']

    def post_api_response(self, *args, **kwargs):
        if not current_user.is_authenticated():
            raise NotAuthorizedApiError
       
        thread_number = int(request.form['thread'])
        board_name = request.form['board']
        state = (request.form['state'] == 'true')

        thread = Thread.query.join(Board).filter(
            Board.name==board_name,
            Thread.number==thread_number
        ).one()
        thread.saved = state
        db.session.commit()

        return {
            'state': thread.saved
        }


class GetParentThread(ApiView):
    """Returns a number of a thread the specified post belongs to."""

    def get_api_response(self, *args, **kwargs):
        post_number = int(request.args['post'])
        board_name = request.args['board']

        try:
            parent_thread_number = Post.query.join(Thread, Board).filter(
                Board.name==board_name,
                Thread.number==post_number
            ).one().thread.number
        except NoResultFound:
            raise NotFoundApiError

        return {
            'parent_thread': parent_thread_number
        }


class SuggestTag(ApiView):
    def get_api_response(self):
        query = request.args['query']
        tags = Tag.query.filter(Tag.name.like('%' + query + '%')).limit(5)
        return {
            'query': query, 
            'suggestions': [tag.name for tag in tags]
        }


class AddTag(ApiView):
    methods = ['POST']

    def post_api_response(self):
        if not current_user.is_authenticated():
            raise NotAuthorizedApiError

        thread_number = int(request.form['thread'])
        board_name = request.form['board']
        tag = request.form['tag']

        try:
            thread = Thread.query.join(Board).filter(
                Thread.number==thread_number, 
                Board.name==board_name
            ).one()
        except NoResultFound:
            raise NotFoundApiError(message='Thread does not exist.')

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

        return {
            'added': added
        }


class RemoveTag(ApiView):
    methods = ['POST']

    def post_api_response(self):
        if not current_user.is_authenticated():
            raise NotAuthorizedApiError

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

        return {
            'removed': True,
            'tag': tag,
        }


bl.add_url_rule('/gallery/', view_func=Gallery.as_view('gallery'))
bl.add_url_rule('/stats/', view_func=Stats.as_view('stats'))
bl.add_url_rule('/status/', view_func=Status.as_view('status'))

bl.add_url_rule('/thread/save/', view_func=SaveThread.as_view('save_thread'))
bl.add_url_rule('/get_parent_thread/', view_func=GetParentThread.as_view('get_parent_thread'))

bl.add_url_rule('/tag/suggest/', view_func=SuggestTag.as_view('suggest_tag'))
bl.add_url_rule('/tag/add/', view_func=AddTag.as_view('add_tag'))
bl.add_url_rule('/tag/remove/', view_func=RemoveTag.as_view('remove_tag'))
