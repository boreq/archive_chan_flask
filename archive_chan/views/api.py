import json

from django.views.generic.base import View
from django.http import HttpResponse

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
            response_data, status_code = self.handle_exception(ApiError())

        return HttpResponse(
            json.dumps(response_data, indent=4),
            content_type='application/json',
            status=status_code
        )

class StatusView(ApiView):
    def get_api_response(self, request, *args, **kwargs):
        raise NotImplementedApiError
