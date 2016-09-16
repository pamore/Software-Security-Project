from login.models import InternalUser, ExternalUser
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class OneLoginPerUserMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print(request.user)
        if isinstance(request.user, User):
            current_key = request.session.session_key
            print("Current session key %s" % current_key)
            if hasattr(request.user, 'internaluser'):
                print("Internal User")
                active_key = request.user.internaluser.session_key
                print("Active key %s" % current_key)
            elif hasattr(request.user, 'externaluser'):
                print("External User")
                active_key = request.user.externaluser.session_key
                print("Active key %s" % current_key)
            else:
                active_key = None
            if active_key != current_key:
                Session.objects.filter(session_key=active_key).delete()
                if hasattr(request.user, 'internaluser'):
                    print("Double Login!!!")
                    request.user.internaluser.session_key = current_key
                    print("New current key %s" % current_key)
                    request.user.internaluser.save()
                elif hasattr(request.user, 'externaluser'):
                    print("Double Login!!!")
                    request.user.externaluser.session_key = current_key
                    print("New current key %s" % current_key)
                    request.user.externaluser.save()
                else:
                    pass
        response = self.get_response(request)
        return response
