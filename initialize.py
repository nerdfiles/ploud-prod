""" frontend initializing """
from zope import interface
from ptah import config, view
from pyramid.security import Allow, Everyone, ALL_PERMISSIONS
from pyramid.i18n import TranslationStringFactory

import ptah
from ptah.settings import PTAH_CONFIG
from ploud.frontend.models import User
from ploud.frontend.root import PloudApplicationRoot
from ploud.themegallery.permissions import GALLERY_ACL

MessageFactory = _ = TranslationStringFactory('ploud.frontend')


class ApplicationPolicy(object):

    __name__ = ''
    __parent__ = None

    def __init__(self, request):
        self.request = request


@config.subscriber(config.AppStarting)
def initialize(ev):
    pconfig = ev.config

    # mount application to '/' location wit custom ApplicationRoot
    factory = ptah.cms.ApplicationFactory(
        PloudApplicationRoot,
        '/', 'root', 'Ptah CMS', ApplicationPolicy, default_root=True)
    pconfig.set_root_factory(factory)

    # give managers all permissions
    acl = [(Allow, Everyone, ptah.cms.View)]
    for login in PTAH_CONFIG.managers:
        user = User.get(login)
        if user is not None:
            acl.append((Allow, user.uri, ALL_PERMISSIONS))
            
            # theme gallery
            GALLERY_ACL.allow(user.uri, ALL_PERMISSIONS)

    ApplicationPolicy.__acl__ = acl
