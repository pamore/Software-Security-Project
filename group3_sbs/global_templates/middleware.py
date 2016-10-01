from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class OneLoginPerUserMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if isinstance(request.user, User):
            current_key = request.session.session_key
            if hasattr(request.user, 'regualaremployee'):
                active_key = request.user.regularemployee.session_key
            elif hasattr(request.user, 'systemmanager'):
                active_key = request.user.systemmanager.session_key
            elif hasattr(request.user, 'administrator'):
                active_key = request.user.administrator.session_key
            elif hasattr(request.user, 'individualcustomer'):
                active_key = request.user.individualcustomer.session_key
            elif hasattr(request.user, 'merchantorganization'):
                active_key = request.user.merchantorganization.session_key
            else:
                active_key = None
            if active_key != current_key:
                Session.objects.filter(session_key=active_key).delete()
                if hasattr(request.user, 'regualaremployee'):
                    request.user.regularemployee.session_key = current_key
                    request.user.regularemployee.save()
                elif hasattr(request.user, 'systemmanager'):
                    request.user.systemmanager.session_key = current_key
                    request.user.systemmanager.save()
                elif hasattr(request.user, 'administrator'):
                    request.user.administrator.session_key = current_key
                    request.user.administrator.save()
                elif hasattr(request.user, 'individualcustomer'):
                    request.user.individualcustomer.session_key = current_key
                    request.user.individualcustomer.save()
                elif hasattr(request.user, 'merchantorganization'):
                    request.user.merchantorganization.session_key = current_key
                    request.user.merchantorganization.save()
                else:
                    pass
        response = self.get_response(request)
        return response
