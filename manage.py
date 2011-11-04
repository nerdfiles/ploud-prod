""" management """
import colander
from pyramid.httpexceptions import HTTPFound
from sqlalchemy.sql.expression import asc

import ptah
from ptah.token import service
from ptah import view, config, form, manage

from ploud.utils import ploud_config
from ploud.utils.policy import POLICIES
from ploud.utils.disable import disableVhosts, enableVhosts

import utils
from config import MNGLOGIN_TOKEN_TYPE
from models import Session, User, Site


class Management(manage.PtahModule):
    """Ploud Frontend management module."""

    title = 'Ploud management'
    manage.module('ploud')

    def __getitem__(self, key):
        try:
            key = int(key)
        except:
            raise KeyError(key)

        user = Session.query(User).filter_by(id=key).first()
        user.__parent__ = self
        user.__name__ = str(key)
        return user


class UsersList(view.View):
    view.pview(context = Management, layout='',
               template = view.template('newui/manage.pt'))

    users = ()
    sites = ()

    def update(self):
        request = self.request

        action = None
        param = request.params.get('search', '')

        if 'searchusers' in request.POST:
            action = 'searchusers'
            request.session['manage_param'] = param
            request.session['manage_action'] = action

        if 'showusers' in request.POST:
            action = 'showusers'
            request.session['manage_param'] = param
            request.session['manage_action'] = action

        if 'searchsites' in request.POST:
            action = 'searchsites'
            request.session['manage_param'] = param
            request.session['manage_action'] = action

        if 'showsites' in request.POST:
            action = 'showsites'
            request.session['manage_param'] = param
            request.session['manage_action'] = action

        if action is None:
            param = request.session.get('manage_param', None)
            action = request.session.get('manage_action', None)

        if action == 'searchusers':
            self.users = Session.query(User)\
                .filter(User.email.contains('%%%s%%'%param))\
                .order_by(asc('id')).all()

        elif action == 'showusers':
            self.users = Session.query(User).order_by(asc('id')).all()

        if action == 'searchsites':
            self.sites = Session.query(Site)\
                .filter(Site.site_name.contains('%%%s%%'%param))\
                .order_by(asc('id')).all()
            self.sites = [site for site in self.sites if not site.removed]

        elif action == 'showsites':
            self.sites = Session.query(Site).order_by(asc('id')).all()
            self.sites = [site for site in self.sites if not site.removed]


policies = form.SimpleVocabulary(
    form.SimpleTerm(0, '0', 'Type 0'),
    form.SimpleTerm(1, '1', 'Type 1'),
    form.SimpleTerm(2, '2', 'Type 2'),
    form.SimpleTerm(98, '98', 'Type 98 (Un-validated)'),
    form.SimpleTerm(99, '99', 'Type 99 (Superuser)'))


PolicySchema = form.Fieldset(
    form.RadioField(
        'policy',
        title = u'Membership type',
        description = u'Choose user membership type.',
        validator = form.OneOf(policies),
        vocabulary = policies)
)


class UserView(form.Form):
    view.pview(context = User,
               template = view.template('newui/userinfo.pt'))

    prefix = 'user_info'
    fields = PolicySchema

    def update(self):
        super(UserView, self).update()

        user = self.context
        request = self.request
        policy = POLICIES[user.type]

        size = 0
        bandwidth = 0
        for site in user.sites:
            if site.removed:
                continue
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
            if site.removed:
                continue

            site_form = SiteForm(user, site, request)
            site_form.update()

            site_infos.append(
                {'id': '%s/%s'%(site.id, site.typeof),
                 'site_id': site.id,
                 'name': site.site_name,
                 'last_accessed': site.last_accessed,
                 'disabled': str(site.disabled),
                 'dbsize': '%0.2fMb (%0.1f%%)'%(
                        site.size/1048576.0, site.size / (size/100.0)),
                 'bandwidth': '%0.2fMb (%0.1f%%)'%(
                        (site.bwin+site.bwout)/1048576.0,
                        (site.bwin+site.bwout) / (bandwidth/100.0)),
                 'form': site_form,
                 'host': site.hosts[0].host})
        self.site_infos = site_infos
        self.sites = len(site_infos)

        self.change_password = ChangePasswordForm(user, request)
        self.change_password.update()

    def form_content(self):
        return {'policy': self.context.type}

    @form.button(u'Update', actype=form.AC_PRIMARY)
    def changeUserType(self):
        data, errors = self.extract()

        if not errors:
            self.message("User's membership type has been change.")

            user = self.context
            if user.type != data['policy']:
                user.type = data['policy']

                conn = ploud_config.PLOUD_POOL.getconn()
                cursor = conn.cursor()
                POLICIES[user.type].apply(user.id, cursor)
                cursor.close()
                conn.commit()
                ploud_config.PLOUD_POOL.putconn(conn)

    @form.button(u'Remove User', actype=form.AC_DANGER)
    def removeHandler(self):
        user = self.context
        Session.delete(user)
        self.message("User has been removed.")
        raise HTTPFound(location='../index.html')


class ChangePasswordForm(form.Form):

    prefix = 'user_password'
    fields = form.Fieldset(
        form.TextField(
            'password',
            title = u'Change password'))

    @form.button('Change', actype=form.AC_PRIMARY)
    def changePassword(self):
        data, errors = self.extract()

        if not errors:
            self.message("Password has been changed.")

            self.context.password = data['password']


class SiteForm(form.Form):

    fields = form.Fieldset(
        form.BoolField(
            'disabled',
            title = u'Disabled'))

    def __init__(self, user, site, request):
        self.context = site
        self.request = request

        self.prefix = 'site%s'%site.id
        self.__paernt__ = user

    def form_content(self):
        return {'disabled': self.context.disabled}

    @form.button(u'Update')
    def updateHandler(self):
        data, errors = self.extract()

        if not errors:
            site = self.context

            if site.disabled != data['disabled']:
                site.disabled = data['disabled']
                print site
                if site.disabled:
                    utils.disableHost(site)
                else:
                    utils.enableHost(site)

            self.message('Site info has been updated.')

    @form.button(u'Remove', actype=form.AC_DANGER)
    def updateHandler(self):
        raise HTTPFound(location='removesite.html?id=%s'%self.context.id)


class RemoveSiteView(form.Form):
    view.pview('removesite.html', User, layout='',
               template = view.template('newui/removesite.pt'))

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
            self.message('Site id is required.')
            raise HTTPFound(location='index.html')

        super(RemoveSiteView, self).update()

    @form.button(u'Remove', actype=form.AC_DANGER)
    def removeHandler(self):
        user = self.context
        conn = ploud_config.PLOUD_POOL.getconn()
        cursor = conn.cursor()

        pol = POLICIES[user.type]
        pol.removeSite(self.site.id, cursor)

        self.site.removed = True
        cursor.close()
        conn.commit()
        ploud_config.PLOUD_POOL.putconn(conn)
        self.message("Site has been removed.")
        raise HTTPFound(location='index.html')

    @form.button(u'Cancel')
    def cancelHandler(self):
        raise HTTPFound(location='index.html')


@view.pview('login', Management)
def managerLogin(request):
    sid = request.params.get('id')

    if sid:
        site = Session.query(Site).filter_by(id=sid).first()
        if site is not None:
            # login
            token = service.generate(MNGLOGIN_TOKEN_TYPE, site.id)
            host = site.hosts[0]
            return HTTPFound(
                location='http://%s/authToken?token=%s'%(host.host, token))

    raise HTTPFound(location='/ptah-manage/ploud/')
