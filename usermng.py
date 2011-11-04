"""

$Id:  2007-12-12 12:27:02Z fafhrd $
"""
from zope import interface, schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from webob.exc import HTTPFound
from pyramid.config import Configurator
from sqlalchemy.sql.expression import asc

from memphis import view, config, form

from ploud.utils import ploud_config
from ploud.utils.policy import POLICIES
from ploud.utils.disable import disableVhosts, enableVhosts

import decorators, models, utils
from models import Session, User


class UserManagement(object):

    __name__ = 'usermanagement'
    __parent__ = view.Root

    def __getitem__(self, key):
        try:
            key = int(key)
        except:
            raise KeyError(key)

        users = Session.query(User).filter_by(id=key).all()
        user = users[0]
        user.__parent__ = self
        user.__name__ = str(key)
        return user


umng = UserManagement()


@config.action
def registerRoute():
    cfg = Configurator.with_context(config.getContext())
    def getMNG(request):
        return umng
    cfg.add_route(
        'ploud.frontend', 'usermanagement/*traverse',
        factory=getMNG, use_global_views = True)


class UsersList(view.View):
    view.pyramidView('index.html', UserManagement,
                     default = True,
                     decorator = decorators.require_manager_login)

    title = 'Users management'
    template = view.template('newui/usermanagement.pt')

    users = ()

    def update(self):
        srch = self.request.params.get('search', '')
        if srch:
            self.users = list(Session.query(User)
                .filter(User.email.contains('%%%s%%'%srch)).order_by(asc('id')).all())
        elif self.request.params.get('showall', ''):
            self.users = list(Session.query(User).order_by(asc('id')).all())


policies = SimpleVocabulary((
        SimpleTerm(0, '0', 'Type 0'),
        SimpleTerm(1, '1', 'Type 1'),
        SimpleTerm(2, '2', 'Type 2'),
        SimpleTerm(99, '99', 'Type 99')))


class IPolicy(interface.Interface):

    policy = schema.Choice(
        title = u'Membership type',
        vocabulary = policies,
        required = True)


class UserView(form.Form, view.View):
    view.pyramidView('index.html', User,
                     default = True,
                     decorator = decorators.require_manager_login)

    prefix = 'user_info'
    fields = form.Fields(IPolicy)
    ignoreContext = False

    template = view.template('newui/userinfo.pt')

    def update(self):
        super(UserView, self).update()

        user = self.context
        request = self.request
        policy = POLICIES[user.type]

        size = 0
        bandwidth = 0
        for site in user.sites:
            size += site.size
            bandwidth += site.bwin
            bandwidth += site.bwout

        self.sites = len(user.sites)
        self.dbsize = '%0.2fMb (%0.1f%%)'%(
            size/1048576.0, size / (policy.dbsize/100.0))
        self.bandwidth = '%0.2fMb (%0.1f%%)'%(
            bandwidth/1048576.0, bandwidth / (policy.bandwidth/100.0))

        site_infos = []
        if not bandwidth:
            bandwidth = 0.000001
        if not size:
            size = 0.000001

        for site in user.sites:
            site_form = SiteForm(user, site, request)
            site_form.update()

            site_infos.append(
                {'id': '%s/%s'%(site.id, site.typeof),
                 'name': site.site_name,
                 'last_accessed': site.last_accessed,
                 'disabled': str(site.disabled),
                 'dbsize': '%0.2fMb (%0.1f%%)'%(
                        site.size/1048576.0, site.size / (size/100.0)),
                 'bandwidth': '%0.2fMb (%0.1f%%)'%(
                        (site.bwin+site.bwout)/1048576.0,
                        (site.bwin+site.bwout) / (bandwidth/100.0)),
                 'form': site_form})
        self.site_infos = site_infos

    def getContent(self):
        return {'policy': self.context.type}

    @form.buttonAndHandler(u'Update')
    def changeUserType(self, action):
        data, errors = self.extractData()

        if not errors:
            view.addMessage(
                self.request,
                "User's membership type has been change.")

            user = self.context
            if user.type != data['policy']:
                user.type = data['policy']

                conn = ploud_config.PLOUD_POOL.getconn()
                cursor = conn.cursor()
                POLICIES[user.type].apply(user.id, cursor)
                cursor.close()
                conn.commit()
                ploud_config.PLOUD_POOL.putconn(conn)


class ISiteForm(interface.Interface):

    disabled = schema.Bool(
        title = u'Disabled',
        )


class SiteForm(form.Form):

    fields = form.Fields(ISiteForm)

    ignoreContext = False

    def __init__(self, user, site, request):
        self.context = site
        self.request = request

        self.prefix = 'site%s'%site.id
        self.__paernt__ = user

    def getContent(self):
        return {'disabled': self.context.disabled}

    @form.buttonAndHandler(u'Update')
    def updateHandler(self, action):
        data, errors = self.extractData()

        if not errors:
            site = self.context

            if site.disabled != data['disabled']:
                site.disabled = data['disabled']
                if site.disabled:
                    utils.disableHost(site)
                else:
                    utils.enableHost(site)

            view.addMessage(self.request, 'Site info has been updated.')

    @form.buttonAndHandler(u'Remove')
    def updateHandler(self, action):
        raise HTTPFound(location='removesite.html?id=%s'%self.context.id)


class RemoveSiteView(form.Form, view.View):
    view.pyramidView('removesite.html', User,
                     decorator = decorators.require_manager_login)

    template = view.template('newui/removesite.pt')

    def update(self):
        site = None
        try:
            id = int(self.request.params.get('id'))
            for s in self.context.sites:
                if s.id == id:
                    site = s
                    break
            if site is not None:
                self.site = site
        except HTTPFound:
            raise
        except:
            pass

        if site is None:
            view.addMessage(self.request, 'Site id is required.')
            raise HTTPFound(location='index.html')

        super(RemoveSiteView, self).update()

    @form.buttonAndHandler(u'Remove')
    def removeHandler(self, action):
        user = self.context
        conn = ploud_config.PLOUD_POOL.getconn()
        cursor = conn.cursor()

        pol = POLICIES[user.type]
        pol.removeSite(self.site.id, cursor)

        site.removed = True
        cursor.close()
        conn.commit()
        ploud_config.PLOUD_POOL.putconn(conn)
        view.addMessage(request, "Site has been removed.")
        raise HTTPFound(location='index.html')

    @form.buttonAndHandler(u'Cancel')
    def removeHandler(self, action):
        raise HTTPFound(location='index.html')
