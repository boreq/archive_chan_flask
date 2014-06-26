import json

from django.db.models import Avg, F
from django.http import HttpResponse
from django.views.generic.base import View

from archive_chan.models import Update

class ApiError(Exception):
    def __init__(self, status_code=500, error_code='unknown', message='Unknown server error.'):
        self.status_code = status_code
        self.error_code = error_code
        super(ApiError, self).__init__(message)

class NotImplementedApiError(ApiError):
    def __init__(self, **kwargs):
        status_code = kwargs.get('status_code', 501)
        error_code = kwargs.get('error_code', 'not_implemented')
        message = kwargs.get('message', 'Not implemented.')
        super(NotImplementedApiError, self).__init__(status_code, error_code, message)

class ApiView(View):
    def handle_exception(self, exception):
        """Extract exception parameters."""
        response_data = {
            'error_code': exception.error_code,
            'message': str(exception),
        }
        return (response_data, exception.status_code)

    def dispatch(self, request, *args, **kwargs):
        """Try to use the right method and handle the exceptions.
        This view will try to get the data from <method_name>_api_response().
        """
        try:
            attr_name = request.method.lower() + '_api_response'
            if request.method.lower() in self.http_method_names and hasattr(self, attr_name):
                response_data = getattr(self, attr_name)(request, *args, **kwargs)
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

        return HttpResponse(
            json.dumps(response_data, indent=4),
            content_type='application/json',
            status=status_code
        )

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
                value = round(entry['average_time'] / entry['average_posts'], 2)
            else:
                value = 0

            chart_data['rows'].append({
                'c': [
                    {'v': value_string, 'f': label_string},
                    {'v': value},
                ]
            })

        return chart_data

    def get_api_response(self, request, *args, **kwargs):
        response_data = {}

        last_update = Update.objects.last()

        response_data['last_update'] = {
            'date': str(last_update.date.isoformat())
        }

        updates = Update.objects.extra({
            'date': 'date("date")'
        }).values('date').order_by('date').annotate(
            average_time=Avg('total_time'),
            average_posts=Avg('added_posts')
        )

        response_data['chart_data'] = self.get_chart_data(updates)

        return response_data
