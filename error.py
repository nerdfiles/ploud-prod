""" errors logging """
from pyramid.httpexceptions import HTTPFound
from pyramid.security import authenticated_userid

import ptah
from ptah import config, view, form, manage
from ploud.frontend import models, decorators
from ploud.frontend.root import PloudApplicationRoot
from ploud.frontend.models import Error, Session


class PloudErrors(manage.PtahModule):
    """Ploud errors module."""

    title = 'Ploud errors'
    manage.module('ploud-errors')

    def __getitem__(self, key):
        try:
            eid = int(key)
        except:
            raise KeyError(key)

        error = Session.query(Error).filter_by(id=eid).first()
        error.__parent__ = self
        error.__name__ = key
        return error


class ErrorsModuleView(view.View):
    view.pview(
        context=PloudErrors, layout='',
        template=view.template('newui/errorsmod.pt'))

    def update(self):
        count = models.Session.query(models.Error).count()
        self.errors = Session.query(Error)\
            .order_by(Error.time.desc()).slice(0,50)


class ErrorView(form.Form):
    view.pview(
        context=Error, layout='',
        template=view.template('newui/error.pt'))

    def fixed(self):
        return self.context.fixed

    def unfixed(self):
        return not self.context.fixed

    @form.button('Resolve', actype=form.AC_INFO, condition=unfixed)
    def resolveHandler(self):
        self.context.fixed = True
        self.message('Error has been marked as fixed.')

    @form.button('Re-Open', actype=form.AC_INFO, condition=fixed)
    def openHandler(self):
        self.context.fixed = False
        self.message('Error has been re-opened.')

    @form.button('Remove', actype=form.AC_DANGER)
    def removeHandler(self):
        Session.delete(self.context)
        self.message('Error has been removed.')
        raise HTTPFound(location='../')


class ErrorsView(view.View):
    view.pview(
        'errors.html', PloudApplicationRoot, layout='',
        permission = decorators.require_object_login,
        template=view.template('newui/errors.pt'))

    error = None
    errors = None

    title = 'Ploud Errors'

    def update(self):
        eid = None
        error = None
        errors = None
        try:
            eid = int(self.request.GET.get('eid'))
        except:
            pass

        if eid:
            error = Session.query(Error).filter_by(id=eid).first()
            if error is not None:
                self.error = error
                return

        count = Session.query(Error).count()
        self.errors = Session.query(Error)\
            .order_by(Error.time.desc()).slice(0,50)
