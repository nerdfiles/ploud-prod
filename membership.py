""" membership """
from ptah import view
from pyramid.security import authenticated_userid

from models import User


view.register_route('frontend-membership', '/membership.html')
view.register_route('frontend-membership1', '/membership-free.html')
view.register_route('frontend-membership2', '/membership-1.html')
view.register_route('frontend-membership3', '/membership-2.html')


class MembershipView(view.View):
    view.pview(route='frontend-membership', layout='page',
               template = view.template('newui/membership.pt'))

    policy = 0

    def update(self):
        uri = authenticated_userid(self.request)
        user = User.getByURI(uri)
        info = {'email': user.email,
                'policy': getattr(user, 'type', 0)}
        self.policy = info['policy']
        self.user = user
        self.isAnon = user is None
        return info


view.register_view(
    route='frontend-membership1', layout='page',
    template = view.template('newui/membership-free.pt'))

view.register_view(
    route='frontend-membership2', layout='page',
    template = view.template('newui/membership1.pt'))

view.register_view(
    route='frontend-membership3', layout='page',
    template = view.template('newui/membership2.pt'))
