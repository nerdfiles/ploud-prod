""" views """
import os.path
from webob import Response
from ptah import view
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid
from root import IPloudApplicationRoot


view.static('ploud', 'ploud.frontend:assets')


class FaviconView(view.View):
    view.pview(route='frontend-favicon', layout=None)

    icon_path = os.path.join(
        os.path.dirname(__file__), 'assets', '_img-ui', 'favicon.ico')

    def render(self):
        response = self.request.response
        response.content_type='image/x-icon'
        return open(self.icon_path).read()


class RobotsView(view.View):
    view.pview(route='frontend-robots', layout=None)

    robots_path = os.path.join(
        os.path.dirname(__file__), 'assets', 'robots.txt')

    def render(self):
        response = self.request.response
        response.content_type = 'text/plain'
        return open(self.robots_path).read()


@view.pview('', IPloudApplicationRoot)
def default(request):
    raise HTTPFound(location='/index.html')


@view.pview(route='frontend-home', layout='page',
                  template = view.template('newui/homepage.pt'))
def homepage(request):
    return {'isanon': 1 if authenticated_userid(request) else 0}


@view.pview(route='frontend-themes')
def themes(request):
    raise HTTPFound(location = '/themes/')


view.register_route('frontend-home', '/index.html')
view.register_route('frontend-favicon', '/favicon.ico')
view.register_route('frontend-robots', '/robots.txt')
view.register_route('frontend-policy', '/privacy-policy.html')
view.register_route('frontend-toc', '/terms-of-service.html')
view.register_route('frontend-disabled', '/disabled.html')
view.register_route('frontend-404', '/404.html')
view.register_route('frontend-themes', '/themes')


view.register_view(
    route='frontend-policy', layout='page',
    template = view.template('newui/privacy-policy.pt'))

view.register_view(
    route='frontend-toc', layout='page',
    template = view.template('newui/terms-of-service.pt'))

view.register_view(
    route='frontend-disabled', layout='page',
    template = view.template('newui/disabled_site.pt'))

view.register_view(
    route='frontend-404', layout='page',
    template = view.template('newui/404.pt'))
