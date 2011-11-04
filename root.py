""" frontend app root """
import ptah.cms
from zope import interface


class IPloudApplicationRoot(interface.Interface):
    pass


class PloudApplicationRoot(ptah.cms.ApplicationRoot):
    interface.implements(IPloudApplicationRoot)

    __type__ = ptah.cms.Type(
        'ploud', 'Ploud app',
        global_allow = False)
