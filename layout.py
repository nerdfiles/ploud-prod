from ptah import view
from pyramid.httpexceptions import HTTPFound
from pyramid.security import forget, authenticated_userid

import ptah
import ptah.cms
from ploud.utils.policy import POLICIES
from ploud.frontend.config import PLOUD, LAYER
from ploud.frontend.root import PloudApplicationRoot

import config
from models import User


view.register_layout(
    'workspace', context=PloudApplicationRoot, parent='page',
    template=view.template('ploud.frontend:newui/layout-workspace.pt'))

view.register_layout(
    '', ptah.cms.IContent, parent="workspace", layer=LAYER,
    template=view.template("ploud.frontend:newui/layout-content.pt"))


class Fake(view.Layout):
    view.layout('', PloudApplicationRoot, parent='page', layer=LAYER)
    
    def render(self, content):
        return content


class MainLayout(view.Layout):
    view.layout('page', PloudApplicationRoot, layer=LAYER)

    template = view.template("newui/layout.pt")

    manager = False

    def update(self):
        super(MainLayout, self).update()

        self.principal = principal = authenticated_userid(self.request)
        self.user = User.getByURI(principal)
        self.isanon = not self.user

        if principal and self.user is None:
            headers = forget(self.request)
            raise HTTPFound(location='/', headers=headers)

        if not self.isanon:
            self.membership = self.user.membership_label()
            self.policy = POLICIES.get(self.user.type, 0)
            if self.user.type in (1, 2):
                self.policy_id = self.user.type
            else:
                self.policy_id = 'free'

            price = config.PRICES.get(self.policy.id, 'free')
            if price == 'free':
                self.price = 'free'
            else:
                self.price = '$%s'%price

            self.removes =  self.policy.removes - self.user.removes
            self.transfers =  self.policy.transfers - self.user.transfers
            sites = len([s for s in self.user.sites if not s.removed])
            self.sites = self.policy.sites - sites

            self.manager = self.user.email in ptah.PTAH_CONFIG.managers
            self.principal = self.user.email
