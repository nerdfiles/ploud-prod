"""Decorators to alter the behavior of view functions."""
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid

from ploud.frontend.config import PLOUD


def require_object_login(context, request):
    """Require that the user be logged in to access the view function."""
    email = authenticated_userid(request)
    if email is None:
        raise HTTPFound(location='/index.html')
    else:
        return True
